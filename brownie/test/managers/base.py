#!/usr/bin/python3

import json
from hashlib import sha1

from py.path import local

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
        config.rootdir = local(project._path)

        self.project = project
        self.project_path = project._path

        self.results = {}
        self.node_map = {}
        self.isolated = {}
        self.skip = {}
        self.contracts = dict(
            (k, v["bytecodeSha1"]) for k, v in project._build.items() if v.get("bytecode")
        )

        glob = self.project_path.glob("tests/**/conftest.py")
        self.conf_hashes = dict((self._path(i.parent), _get_ast_hash(i)) for i in glob)
        try:
            with self.project_path.joinpath("build/tests.json").open() as fp:
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

        Removes `PytestAssertRewriteWarning` warnings from the terminalreporter.
        This prevents warnings that "the `brownie` library was already imported and
        so related assertions cannot be rewritten". The warning is not relevant
        for end users who are performing tests with brownie, not on brownie,
        so we suppress it to avoid confusion.

        Removal of pytest warnings must be handled in this hook because session
        information is passed between xdist workers and master prior to test execution.
        """
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

    def pytest_terminal_summary(self, terminalreporter):
        """
        Add a section to terminal summary reporting.

        When the `--disable-warnings` flag is active, removes all raised warnings
        prior to outputting the final console report.

        Arguments
        ---------
        terminalreporter : `_pytest.terminal.TerminalReporter`
            the internal terminal reporter object
        """
        if self.config.getoption("--disable-warnings") and "warnings" in terminalreporter.stats:
            del terminalreporter.stats["warnings"]

    def _sessionfinish_coverage(self, coverage_eval):
        if CONFIG.argv["coverage"]:
            output._print_coverage_totals(self.project._build, coverage_eval)
            output._save_coverage_report(
                self.project._build, coverage_eval, self.project_path.joinpath("reports")
            )

    def pytest_keyboard_interrupt(self):
        CONFIG.argv["interrupt"] = True
