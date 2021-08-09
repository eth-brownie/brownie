#!/usr/bin/python3

import json
from hashlib import sha1
from pathlib import Path

import hypothesis

import brownie
from brownie._config import CONFIG
from brownie.project.scripts import _get_ast_hash
from brownie.test import _apply_given_wrapper, coverage, output

from .utils import convert_outcome


class PytestBrownieBase:
    """
    Brownie plugin base hooks.

    Pytest hooks in this class are used in every testing mode.
    """

    def __init__(self, config, project):
        _apply_given_wrapper()

        self.config = config
        # required when brownie project is in a subfolder of another project
        config._rootpath = Path(project._path)

        self.project = project
        self.project_path = project._path

        self.results = {}
        self.node_map = {}
        self.isolated = {}
        self.skip = {}
        self.contracts = dict(
            (k, v["bytecodeSha1"]) for k, v in project._build.items() if v.get("bytecode")
        )

        glob = self.project_path.joinpath(self.project._structure["tests"]).glob("**/conftest.py")
        self.conf_hashes = dict((self._path(i.parent), _get_ast_hash(i)) for i in glob)
        try:
            with self.project._build_path.joinpath("tests.json").open() as fp:
                hashes = json.load(fp)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            hashes = {"tests": {}, "contracts": {}, "tx": {}}

        self.tests = dict(
            (k, v)
            for k, v in hashes["tests"].items()
            if self.project_path.joinpath(k).exists() and self._get_hash(k) == v["sha1"]
        )

        changed_contracts = set(
            k
            for k, v in hashes["contracts"].items()
            if k not in self.contracts or v != self.contracts[k]
        )
        if changed_contracts:
            for txhash, coverage_eval in hashes["tx"].items():
                if not changed_contracts.intersection(coverage_eval.keys()):
                    coverage._add_cached_transaction(txhash, coverage_eval)
            self.tests = dict(
                (k, v)
                for k, v in self.tests.items()
                if v["isolated"] is not False and not changed_contracts.intersection(v["isolated"])
            )
        else:
            for txhash, coverage_eval in hashes["tx"].items():
                coverage._add_cached_transaction(txhash, coverage_eval)

    def _reduce_path_strings(self, text):
        # convert absolute path strings to relative ones, prior to outputting to console
        base_path = f"{Path(brownie.__file__).parent.as_posix()}"
        project_path = f"{self.project_path.as_posix()}/"

        text = text.replace(base_path, "brownie")
        text = text.replace(project_path, "")
        return text

    def _path(self, path):
        return self.project_path.joinpath(path).relative_to(self.project_path).as_posix()

    def _test_id(self, nodeid):
        path, test_id = nodeid.split("::", maxsplit=1)
        return self._path(path), test_id

    def _get_hash(self, path):
        hash_ = _get_ast_hash(self.project_path.joinpath(path))
        for confpath in filter(lambda k: k in path, sorted(self.conf_hashes)):
            hash_ += self.conf_hashes[confpath]
        return sha1(hash_.encode()).hexdigest()

    def pytest_configure(self, config):
        config.addinivalue_line(
            "markers", "require_network: only run test when a specific network is active"
        )
        config.addinivalue_line(
            "markers", "skip_coverage: skips a test when coverage evaluation is active"
        )
        config.addinivalue_line(
            "markers", "no_call_coverage: do not evaluate coverage for calls made during a test"
        )

        for key in ("coverage", "always_transact"):
            CONFIG.argv[key] = config.getoption("--coverage")
        CONFIG.argv["cli"] = "test"
        CONFIG.argv["gas"] = config.getoption("--gas")
        CONFIG.argv["revert"] = config.getoption("--revert-tb")
        CONFIG.argv["update"] = config.getoption("--update")
        CONFIG.argv["network"] = None
        if config.getoption("--network"):
            CONFIG.argv["network"] = config.getoption("--network")[0]

    def _make_nodemap(self, ids):
        self.node_map.clear()
        for item in ids:
            path, test = self._test_id(item)
            self.node_map.setdefault(path, []).append(test)

    def pytest_sessionstart(self):
        """
        Called after the `Session` object has been created and before performing
        collection and entering the run test loop.

        * Replaces the default hypothesis reporter with a one that applies source
          highlights and increased vertical space between results. The effect is
          seen in output for `hypothesis.errors.MultipleFailures` and while the
          `-v` flag is active.

        * Removes `PytestAssertRewriteWarning` warnings from the terminalreporter.
          This prevents warnings that "the `brownie` library was already imported and
          so related assertions cannot be rewritten". The warning is not relevant
          for end users who are performing tests with brownie, not on brownie,
          so we suppress it to avoid confusion.

        Removal of pytest warnings must be handled in this hook because session
        information is passed between xdist workers and master prior to test execution.
        """

        def _hypothesis_reporter(text):
            text = self._reduce_path_strings(text)
            if next((i for i in ("Falsifying", "Trying", "Traceback") if text.startswith(i)), None):
                print("")

            lines = [
                reporter._tw._highlight(i) if not i.lstrip().startswith("\x1b") else f"{i}\n"
                for i in text.split("\n")
            ]
            text = "".join(lines)

            end = "\n" if text.startswith("Traceback") else ""
            print(text, end=end)

        hypothesis.reporting.reporter.default = _hypothesis_reporter
        hypothesis.extra.pytestplugin.default_reporter = _hypothesis_reporter

        reporter = self.config.pluginmanager.get_plugin("terminalreporter")
        warnings = reporter.stats.pop("warnings", [])
        warnings = [i for i in warnings if "PytestAssertRewriteWarning" not in i.message]
        if warnings and not self.config.getoption("--disable-warnings"):
            reporter.stats["warnings"] = warnings

    def pytest_report_teststatus(self, report):
        """
        Return result-category, shortletter and verbose word for status reporting.

        With the `--update` flag, modifies the outcome of already-run skipped
        tests so that the final report shows accurate pass/fail information.

        Arguments
        ---------
        report : _pytest.reports.BaseReport
            Report object for the current test.
        """
        if report.when == "setup":
            self.skip[report.nodeid] = report.skipped
            if report.failed:
                return "error", "E", "ERROR"
            return "", "", ""
        if report.when == "teardown":
            if report.failed:
                return "error", "E", "ERROR"
            elif self.skip[report.nodeid]:
                path, test_id = self._test_id(report.nodeid)
                idx = self.node_map[path].index(test_id)
                report.outcome = convert_outcome(self.results[path][idx])
                return "skipped", "s", "SKIPPED"
            return "", "", ""
        if hasattr(report, "wasxfail"):
            if report.skipped:
                return "xfailed", "x", "XFAIL"
            elif report.passed:
                return "xpassed", "X", "XPASS"
        return report.outcome, convert_outcome(report.outcome), report.outcome.upper()

    def pytest_runtest_makereport(self, item):
        """
        Return a _pytest.runner.TestReport object for the given pytest.Item and
        _pytest.runner.CallInfo.

        Applies source highlighting to hypothesis output that is not related to
        `hypothesis.errors.MultipleFailures`.

        Attributes
        ----------
        item : pytest.Item
            Object representing the currently active test
        """
        if not hasattr(item, "hypothesis_report_information"):
            return

        reporter = self.config.pluginmanager.get_plugin("terminalreporter")

        report = [x for i in item.hypothesis_report_information for x in i.split("\n")]
        report = [self._reduce_path_strings(i) for i in report]
        report = [
            reporter._tw._highlight(i).rstrip("\n") if not i.lstrip().startswith("\x1b") else i
            for i in report
        ]

        item.hypothesis_report_information = report

    def pytest_terminal_summary(self, terminalreporter):
        """
        Add a section to terminal summary reporting.

        * When the `--disable-warnings` flag is active, removes all raised warnings
          prior to outputting the final console report.

        * When `--coverage` is active, outputs the result to stdout and saves the
          final report json.

        Arguments
        ---------
        terminalreporter : `_pytest.terminal.TerminalReporter`
            The internal terminal reporter object
        """
        if self.config.getoption("--disable-warnings") and "warnings" in terminalreporter.stats:
            del terminalreporter.stats["warnings"]

        if CONFIG.argv["coverage"]:
            terminalreporter.section("Coverage")

            # output coverage report to console
            coverage_eval = coverage.get_merged_coverage_eval()
            for line in output._build_coverage_output(coverage_eval):
                terminalreporter.write_line(line)

            # save coverage report as `reports/coverage.json`
            output._save_coverage_report(
                self.project._build,
                coverage_eval,
                self.project_path.joinpath(self.project._structure["reports"]),
            )

    def pytest_unconfigure(self):
        """
        Called before test process is exited.

        Closes all active projects.
        """
        for project in brownie.project.get_loaded_projects():
            project.close(raises=False)

    def pytest_keyboard_interrupt(self):
        CONFIG.argv["interrupt"] = True
