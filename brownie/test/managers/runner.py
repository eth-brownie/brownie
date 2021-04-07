#!/usr/bin/python3

import builtins
import json
import re
import sys
import warnings
from pathlib import Path

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

SCOPE_ORDER = ("session", "package", "module", "class", "function")


def _make_fixture_execute_first(metafunc, name, scope):
    fixtures = metafunc.fixturenames

    scopes = SCOPE_ORDER[SCOPE_ORDER.index(scope) :]
    if name in fixtures:
        fixtures.remove(name)
        defs = metafunc._arg2fixturedefs
        idx = next(
            (fixtures.index(i) for i in fixtures if i in defs and defs[i][0].scope in scopes),
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
    def __init__(
        self, revert_msg=None, dev_revert_msg=None, revert_pattern=None, dev_revert_pattern=None
    ):
        if revert_msg is not None and revert_pattern is not None:
            raise ValueError("Can only use one of`revert_msg` and `revert_pattern`")
        if dev_revert_msg is not None and dev_revert_pattern is not None:
            raise ValueError("Can only use one of `dev_revert_msg` and `dev_revert_pattern`")

        if revert_pattern:
            re.compile(revert_pattern)
        if dev_revert_pattern:
            re.compile(dev_revert_pattern)

        self.revert_msg = revert_msg
        self.dev_revert_msg = dev_revert_msg
        self.revert_pattern = revert_pattern
        self.dev_revert_pattern = dev_revert_pattern
        self.always_transact = CONFIG.argv["always_transact"]

        if revert_msg is not None and (revert_msg.startswith("dev:") or dev_revert_msg):
            # run calls as transactinos when catching a dev revert string
            CONFIG.argv["always_transact"] = True

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        CONFIG.argv["always_transact"] = self.always_transact

        if exc_type is None:
            raise AssertionError("Transaction did not revert")

        if exc_type is not VirtualMachineError:
            raise

        if self.dev_revert_msg or self.dev_revert_pattern:
            actual = exc_value.dev_revert_msg
            if (
                actual is None
                or (self.dev_revert_pattern and not re.fullmatch(self.dev_revert_pattern, actual))
                or (self.dev_revert_msg and self.dev_revert_msg != actual)
            ):
                raise AssertionError(
                    f"Unexpected dev revert string '{actual}'\n{exc_value.source}"
                ) from None

        if self.revert_msg or self.revert_pattern:
            actual = exc_value.revert_msg
            if (
                actual is None
                or (self.revert_pattern and not re.fullmatch(self.revert_pattern, actual))
                or (self.revert_msg and self.revert_msg != actual)
            ):
                raise AssertionError(
                    f"Unexpected revert string '{actual}'\n{exc_value.source}"
                ) from None

        return True


class PytestPrinter:
    """
    Custom printer for test execution.

    Produces more-readable output when stdout capture is disabled.
    """

    _builtins_print = builtins.print

    def start(self):
        self.first_line = True
        builtins.print = self

    def __call__(self, *values, sep=" ", end="\n", file=sys.stdout, flush=False):
        if file != sys.stdout:
            self._builtins_print(*values, sep=sep, end=end, file=file, flush=flush)
            return

        if self.first_line:
            self.first_line = False
            sys.stdout.write(f"{color('yellow')}RUNNING{color}\n")
        text = f"{sep.join(str(i) for i in values)}{end}"
        sys.stdout.write(text)
        if flush:
            sys.stdout.flush()

    def finish(self, nodeid):
        if not self.first_line:
            sys.stdout.write(f"{nodeid} ")
            sys.stdout.flush()
        builtins.print = self._builtins_print


class PytestBrownieRunner(PytestBrownieBase):
    """
    Brownie plugin runner hooks.

    Hooks in this class are loaded when running without xdist, and by xdist
    worker processes.
    """

    def __init__(self, config, project):
        super().__init__(config, project)
        brownie.reverts = RevertContextManager
        pytest.reverts = revert_deprecation
        self.printer = None
        if config.getoption("capture") == "no":
            self.printer = PytestPrinter()

    def pytest_generate_tests(self, metafunc):
        """
        Generate parametrized calls to a test function.

        Ensure that `module_isolation` and `fn_isolation` are always the
        first fixtures to run within their respective scopes.

        Arguments
        ---------
        metafunc : _pytest.python.Metafunc
            Used to inspect a test function generate tests according to test
            configuration or values specified in the class or module where a
            test function is defined.
        """
        # module_isolation always runs before other module scoped functions
        _make_fixture_execute_first(metafunc, "module_isolation", "module")
        # fn_isolation always runs before other function scoped fixtures
        _make_fixture_execute_first(metafunc, "fn_isolation", "function")

    def pytest_collection_modifyitems(self, items):
        """
        Called after collection has been performed, may filter or re-order the
        items in-place.

        Determines which modules are isolated, and skips tests based on
        the `--update` and `--stateful` flags.

        Arguments
        ---------
        items : List[_pytest.nodes.Item]
            List of item objects representing the collected tests
        """

        stateful = self.config.getoption("--stateful")
        self._make_nodemap([i.nodeid for i in items])

        tests = {}
        for i in items:
            # apply --stateful flag
            if stateful is not None:
                if stateful == "true" and "state_machine" not in i.fixturenames:
                    i.add_marker("skip")
                elif stateful == "false" and "state_machine" in i.fixturenames:
                    i.add_marker("skip")

            # determine which modules are isolated
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

    @pytest.hookimpl(trylast=True, hookwrapper=True)
    def pytest_collection_finish(self, session):
        """
        Called after collection has been performed and modified.

        This is the final hookpoint that executes prior to running tests. If
        the number of tests collected is > 0 and there is not an active network
        at this point, Brownie connects to the the default network and launches
        the RPC client if required.

        Arguments
        ---------
        session : pytest.Session
            The pytest session object.
        """
        outcome = yield
        # handled as a hookwrapper to ensure connecting is the last action for this hook
        if not outcome.get_result() and session.items and not brownie.network.is_connected():
            brownie.network.connect(CONFIG.argv["network"])

    def pytest_runtest_protocol(self, item):
        """
        Implements the runtest_setup/call/teardown protocol for the given test item,
        including capturing exceptions and calling reporting hooks.

        * With the `-s` flag, enable custom stdout handling
        * When the test is from a new module, creates an entry in `self.results`
          and populates it with previous outcomes (if available).

        Arguments
        ---------
        item : _pytest.nodes.Item
            Test item for which the runtest protocol is performed.
        """
        # enable custom stdout
        if self.printer:
            self.printer.start()

        path, test = self._test_id(item.nodeid)
        if path not in self.results:
            if path in self.tests and CONFIG.argv["update"]:
                self.results[path] = list(self.tests[path]["results"])
            else:
                # all tests are initially marked as skipped
                self.results[path] = ["s"] * len(self.node_map[path])

    def pytest_runtest_setup(self, item):
        """
        Called to perform the setup phase for a test item.

        * The `require_network` marker is applied.

        Arguments
        ---------
        item : _pytest.nodes.Item
            Test item for which setup is performed.
        """
        # `require_network` marker logic
        marker = next(item.iter_markers(name="require_network"), None)
        if marker is not None:
            if not len(marker.args):
                raise ValueError("`require_network` marker must include a network name")
            if brownie.network.show_active() not in marker.args:
                pytest.skip("Active network does not match `require_network` marker")
                return

        if CONFIG.argv["coverage"] and (
            next(item.iter_markers(name="skip_coverage"), None)
            or "skip_coverage" in item.fixturenames
        ):
            pytest.skip("`skip_coverage` marker and coverage is active")

    def pytest_runtest_logreport(self, report):
        """
        Process a test setup/call/teardown report relating to the respective phase
        of executing a test.

        * Updates isolation data for the given test module
        * Stores the outcome of the test in `self.results`
        * During teardown of the final test in a given module, resets coverage
          data and records results for that module in `self.tests`

        Arguments
        ---------
        report : _pytest.reports.BaseReport
            Report object for the current test.
        """
        path, test_id = self._test_id(report.nodeid)
        idx = self.node_map[path].index(test_id)

        # update module isolation data
        if path in self.isolated:
            self.isolated[path].update(
                [i for i in _get_current_dependencies() if i in self.contracts]
            )

        # save results for this test
        results = self.results[path]
        if not self.skip.get(report.nodeid):
            if report.when == "call":
                results[idx] = convert_outcome(report.outcome)
                if hasattr(report, "wasxfail"):
                    results[idx] = "x" if report.skipped else "X"
            elif report.failed:
                results[idx] = "E"
        if report.when != "teardown" or idx < len(self.node_map[path]) - 1:
            return

        # record and reset coverage data
        txhash = coverage._get_active_txlist()
        coverage._clear_active_txlist()
        if not CONFIG.argv["coverage"] and (path in self.tests and self.tests[path]["coverage"]):
            # if coverage is not active but we already have coverage data from
            # a previous run, retain the previous data
            txhash = self.tests[path]["txhash"]

        # save module test results
        isolated = False
        if path in self.isolated:
            isolated = sorted(self.isolated[path])
        is_cov = CONFIG.argv["coverage"] or (path in self.tests and self.tests[path]["coverage"])
        self.tests[path] = {
            "sha1": self._get_hash(path),
            "isolated": isolated,
            "coverage": is_cov,
            "txhash": txhash,
            "results": "".join(self.results[path]),
        }

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item):
        """
        Called to run the test for test item (the call phase).

        * Handles logic for the `always_transact` marker.

        Arguments
        ---------
        item : _pytest.nodes.Item
            Test item for which setup is performed.
        """
        no_call_coverage = next(item.iter_markers(name="no_call_coverage"), None)
        if no_call_coverage:
            CONFIG.argv["always_transact"] = False

        yield

        if no_call_coverage:
            CONFIG.argv["always_transact"] = CONFIG.argv["coverage"]

    def pytest_report_teststatus(self, report):
        """
        Return result-category, shortletter and verbose word for status reporting.
        Stops at first non-None result.

        With the `-s` flag, disables `PytestPrinter` prior to the teardown phase
        of each test.

        Arguments
        ---------
        report : _pytest.reports.BaseReport
            Report object for the current test.
        """
        if self.printer and report.when == "call":
            self.printer.finish(report.nodeid)

        return super().pytest_report_teststatus(report)

    def pytest_exception_interact(self, report, call):
        """
        Called when an exception was raised which can potentially be
        interactively handled.

        With the `--interactive` flag, outputs the full repr of the failed test
        and opens an interactive shell using `brownie._cli.console.Console`.

        Arguments
        ---------
        report : _pytest.reports.BaseReport
            Report object for the failed test.
        call : _pytest.runner.CallInfo
            Result/Exception info for the failed test.
        """
        if self.config.getoption("interactive") and report.failed:
            location = self._path(report.location[0])
            if location not in self.node_map:
                # if the exception happened prior to collection it is likely a
                # SyntaxError and we cannot open an interactive debugger
                return

            capman = self.config.pluginmanager.get_plugin("capturemanager")
            if capman:
                capman.suspend_global_capture(in_=True)

            tw = TerminalWriter()
            report.longrepr.toterminal(tw)

            # find the last traceback frame within the active project
            traceback = call.excinfo.traceback[-1]
            for tb_frame in call.excinfo.traceback[::-1]:
                try:
                    Path(tb_frame.path).relative_to(self.project_path)
                    traceback = tb_frame
                    break
                except ValueError:
                    pass

            # get global namespace
            globals_dict = traceback.frame.f_globals

            # filter python internals and pytest internals
            globals_dict = {k: v for k, v in globals_dict.items() if not k.startswith("__")}
            globals_dict = {k: v for k, v in globals_dict.items() if not k.startswith("@")}

            # filter test functions and fixtures
            test_names = self.node_map[location]
            globals_dict = {k: v for k, v in globals_dict.items() if k not in test_names}
            globals_dict = {
                k: v for k, v in globals_dict.items() if not hasattr(v, "_pytestfixturefunction")
            }

            # get local namespace
            locals_dict = traceback.locals
            locals_dict = {k: v for k, v in locals_dict.items() if not k.startswith("@")}

            namespace = {"_callinfo": call, **globals_dict, **locals_dict}
            if "tx" not in namespace and brownie.history:
                # make it easier to look at the most recent transaction
                namespace["tx"] = brownie.history[-1]

            try:
                CONFIG.argv["cli"] = "console"
                shell = Console(self.project, extra_locals=namespace, exit_on_continue=True)
                banner = (
                    "\nInteractive mode enabled. Type `continue` to"
                    " resume testing or `quit()` to halt execution."
                )
                shell.interact(banner=banner, exitmsg="")
            except SystemExit as exc:
                if exc.code != "continue":
                    pytest.exit("Test execution halted due to SystemExit")
            finally:
                CONFIG.argv["cli"] = "test"

            print("Continuing tests...")
            if capman:
                capman.resume_global_capture()

    def pytest_sessionfinish(self):
        """
        Called after whole test run finished, right before returning the exit
        status to the system.

        Stores test results in `build/tests.json`.
        """
        self._sessionfinish("tests.json")

    def _sessionfinish(self, path):
        # store test results at the given path
        txhash = set(x for v in self.tests.values() for x in v["txhash"])
        coverage_eval = dict((k, v) for k, v in coverage.get_coverage_eval().items() if k in txhash)
        report = {"tests": self.tests, "contracts": self.contracts, "tx": coverage_eval}

        with self.project._build_path.joinpath(path).open("w") as fp:
            json.dump(report, fp, indent=2, sort_keys=True, default=sorted)

    def pytest_terminal_summary(self, terminalreporter):
        """
        Add a section to terminal summary reporting.

        When `--gas` is active, outputs the gas profile report.

        Arguments
        ---------
        terminalreporter : `_pytest.terminal.TerminalReporter`
            The internal terminal reporter object
        """
        if CONFIG.argv["gas"]:
            terminalreporter.section("Gas Profile")
            for line in output._build_gas_profile_output():
                terminalreporter.write_line(line)

        super().pytest_terminal_summary(terminalreporter)


class PytestBrownieXdistRunner(PytestBrownieRunner):
    """
    Brownie plugin xdist worker hooks.

    Hooks in this class are loaded on worker processes when using xdist.
    """

    def __init__(self, config, project):
        self.workerid = int("".join(i for i in config.workerinput["workerid"] if i.isdigit()))

        # network ID is passed to the worker via `pytest_configure_node` in the master
        network_id = config.workerinput["network"] or CONFIG.settings["networks"]["default"]
        CONFIG.networks[network_id]["cmd_settings"]["port"] += self.workerid

        super().__init__(config, project)

    def pytest_collection_modifyitems(self, items):
        """
        Called after collection has been performed, may filter or re-order the
        items in-place.

        If any tests do not use the `module_isolation` fixture, all tests are
        discarded. This in turn causes `PytestBrownieMaster.pytest_sessionfinish`
        to raise an exception notifying the user that xdist may only be used
        when tests are properly isolated.

        Arguments
        ---------
        items : List[_pytest.nodes.Item]
            List of item objects representing the collected tests
        """
        if next((i for i in items if "module_isolation" not in i.fixturenames), False):
            items.clear()
            return True

        super().pytest_collection_modifyitems(items)

    def pytest_sessionfinish(self):
        """
        Called after whole test run finished, right before returning the exit
        status to the system.

        Stores test results in `build/tests-{workerid}.json`. Each of these files
        is then aggregated in `PytestBrownieMaster.pytest_sessionfinish`.
        """
        self.tests = dict((k, v) for k, v in self.tests.items() if k in self.results)
        self._sessionfinish(f"tests-{self.workerid}.json")
