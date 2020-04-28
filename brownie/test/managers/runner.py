#!/usr/bin/python3

import builtins
import json
import sys
import warnings

import pytest
from _pytest._io import TerminalWriter

import brownie
from brownie._cli.console import Console
from brownie._config import CONFIG
from brownie.exceptions import VirtualMachineError
from brownie.network.state import _get_current_dependencies
from brownie.test import coverage, output
from brownie.utils import color

from .base import PytestBrownieBase
from .utils import convert_outcome


def _make_fixture_execute_first(metafunc, name, scope):
    fixtures = metafunc.fixturenames
    if name in fixtures:
        fixtures.remove(name)
        defs = metafunc._arg2fixturedefs
        idx = next(
            (fixtures.index(i) for i in fixtures if i in defs and defs[i][0].scope == scope),
            len(fixtures),
        )
        fixtures.insert(idx, name)


def revert_deprecation(revert_msg=None):
    warnings.warn(
        "pytest.reverts has been deprecated, use brownie.reverts instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return RevertContextManager(revert_msg)


class RevertContextManager:
    def __init__(self, revert_msg=None):
        self.revert_msg = revert_msg

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        __tracebackhide__ = True
        if exc_type is None:
            raise AssertionError("Transaction did not revert") from None
        if exc_type is not VirtualMachineError:
            raise exc_type(exc_value).with_traceback(traceback)
        if self.revert_msg is None or self.revert_msg == exc_value.revert_msg:
            return True
        raise AssertionError(
            f"Unexpected revert string '{exc_value.revert_msg}'\n{exc_value.source}"
        ) from None


class PytestPrinter:
    """
    Custom printer for test execution.

    Produces more-readable output when stdout capture is disabled.
    """

    _builtins_print = builtins.print

    def start(self):
        self.first_line = True
        builtins.print = self

    def __call__(self, text):
        if self.first_line:
            self.first_line = False
            sys.stdout.write(f"{color('yellow')}RUNNING{color}\n")
        sys.stdout.write(f"{text}\n")
        sys.stdout.flush()

    def finish(self, nodeid):
        if not self.first_line:
            sys.stdout.write(f"{nodeid} ")
            sys.stdout.flush()
        builtins.print = self._builtins_print


class PytestBrownieRunner(PytestBrownieBase):
    def __init__(self, config, project):
        super().__init__(config, project)
        brownie.reverts = RevertContextManager
        pytest.reverts = revert_deprecation
        self.printer = None
        if config.getoption("capture") == "no":
            self.printer = PytestPrinter()

    def pytest_generate_tests(self, metafunc):
        # module_isolation always runs before other module scoped functions
        _make_fixture_execute_first(metafunc, "module_isolation", "module")
        # fn_isolation always runs before other function scoped fixtures
        _make_fixture_execute_first(metafunc, "fn_isolation", "function")

    def pytest_collection_modifyitems(self, items):
        stateful = self.config.getoption("--stateful")
        self._make_nodemap([i.nodeid for i in items])

        # determine which modules are properly isolated
        tests = {}
        for i in items:
            if "skip_coverage" in i.fixturenames and CONFIG.argv["coverage"]:
                i.add_marker("skip")
            if stateful is not None:
                if stateful == "true" and "state_machine" not in i.fixturenames:
                    i.add_marker("skip")
                elif stateful == "false" and "state_machine" in i.fixturenames:
                    i.add_marker("skip")
            path = self._path(i.parent.fspath)
            if "module_isolation" not in i.fixturenames:
                tests[path] = None
                continue
            if path in tests and tests[path] is None:
                continue
            tests.setdefault(path, []).append(i)
        isolated_tests = sorted(k for k, v in tests.items() if v)
        self.isolated = dict((self._path(i), set()) for i in isolated_tests)

        if CONFIG.argv["update"]:
            isolated_tests = sorted(filter(self._check_updated, tests))
            # if update flag is active, add skip marker to unchanged tests
            for path in isolated_tests:
                tests[path][0].parent.add_marker("skip")
                self.isolated[path] = set(self.tests[path]["isolated"])

        # only connect to network if there are tests to run
        to_run = any(i for i in items if not i.get_closest_marker("skip"))
        if to_run and not self.config.getoption("--fixtures"):
            brownie.network.connect(CONFIG.argv["network"])

    def _check_updated(self, path):
        path = self._path(path)
        if path not in self.tests or not self.tests[path]["isolated"]:
            return False
        if CONFIG.argv["coverage"] and not self.tests[path]["coverage"]:
            return False
        for txhash in self.tests[path]["txhash"]:
            coverage._check_cached(txhash, False)
        return True

    def _make_nodemap(self, ids):
        self.node_map.clear()
        for item in ids:
            path, test = self._test_id(item)
            self.node_map.setdefault(path, []).append(test)

    def pytest_runtest_protocol(self, item):
        # does not run on master
        if self.printer:
            self.printer.start()

        path, test = self._test_id(item.nodeid)
        if path not in self.results:
            if path in self.tests and CONFIG.argv["update"]:
                self.results[path] = list(self.tests[path]["results"])
            else:
                # all tests are initially marked as skipped
                self.results[path] = ["s"] * len(self.node_map[path])

    def pytest_runtest_logreport(self, report):
        path, test_id = self._test_id(report.nodeid)
        if path in self.isolated:
            self.isolated[path].update(
                [i for i in _get_current_dependencies() if i in self.contracts]
            )
        idx = self.node_map[path].index(test_id)

        results = self.results[path]
        if report.when == "call":
            results[idx] = convert_outcome(report.outcome)
            if hasattr(report, "wasxfail"):
                results[idx] = "x" if report.skipped else "X"
        elif report.failed:
            results[idx] = "E"
        if report.when != "teardown" or idx < len(self.node_map[path]) - 1:
            return

        isolated = False
        if path in self.isolated:
            isolated = sorted(self.isolated[path])

        txhash = coverage._get_active_txlist()
        coverage._clear_active_txlist()
        if not CONFIG.argv["coverage"] and (path in self.tests and self.tests[path]["coverage"]):
            txhash = self.tests[path]["txhash"]
        self.tests[path] = {
            "sha1": self._get_hash(path),
            "isolated": isolated,
            "coverage": CONFIG.argv["coverage"]
            or (path in self.tests and self.tests[path]["coverage"]),
            "txhash": txhash,
            "results": "".join(self.results[path]),
        }

    def pytest_report_teststatus(self, report):
        if self.printer and report.when == "call":
            self.printer.finish(report.nodeid)

        return super().pytest_report_teststatus(report)

    def pytest_exception_interact(self, report):
        """
        Called when an exception was raised which can potentially be
        interactively handled.

        With the `--interactive` flag, outputs the full repr of the failed test
        and opens an interactive shell using `brownie._cli.console.Console`.

        Arguments
        ---------
        report : _pytest.reports.BaseReport
            Report object for the failed test.
        """
        if self.config.getoption("interactive") and report.failed:
            capman = self.config.pluginmanager.get_plugin("capturemanager")
            if capman:
                capman.suspend_global_capture(in_=True)

            tw = TerminalWriter()
            report.longrepr.toterminal(tw)
            try:
                shell = Console(self.project)
                shell.interact(
                    banner=f"\nInteractive mode enabled. Use quit() to continue running tests.",
                    exitmsg="",
                )
            except SystemExit:
                pass

            print("Continuing tests...")
            if capman:
                capman.resume_global_capture()

    def pytest_sessionfinish(self):
        self._sessionfinish("build/tests.json")
        if CONFIG.argv["gas"]:
            output._print_gas_profile()

    def _sessionfinish(self, path):
        txhash = set(x for v in self.tests.values() for x in v["txhash"])
        coverage_eval = dict((k, v) for k, v in coverage.get_coverage_eval().items() if k in txhash)
        report = {"tests": self.tests, "contracts": self.contracts, "tx": coverage_eval}

        with self.project_path.joinpath(path).open("w") as fp:
            json.dump(report, fp, indent=2, sort_keys=True, default=sorted)
        coverage_eval = coverage.get_merged_coverage_eval()
        self._sessionfinish_coverage(coverage_eval)
        self.project.close()


class PytestBrownieXdistRunner(PytestBrownieRunner):
    def __init__(self, config, project):
        self.workerid = int("".join(i for i in config.workerinput["workerid"] if i.isdigit()))
        # TODO fix me
        key = CONFIG.argv["network"] or CONFIG.settings["networks"]["default"]
        CONFIG.networks[key]["cmd_settings"]["port"] += self.workerid
        super().__init__(config, project)

    def pytest_collection_modifyitems(self, items):
        # clear collection if isolation is not active
        if next((i for i in items if "module_isolation" not in i.fixturenames), False):
            items.clear()
            return True
        super().pytest_collection_modifyitems(items)

    def pytest_sessionfinish(self):
        self.tests = dict((k, v) for k, v in self.tests.items() if k in self.results)
        self._sessionfinish(f"build/tests-{self.workerid}.json")
