#!/usr/bin/python3

import json

import pytest

from brownie import network
from brownie._config import ARGV, CONFIG
from brownie.exceptions import VirtualMachineError
from brownie.network.state import _get_current_dependencies
from brownie.test import coverage, output

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


class PytestBrownieRunner(PytestBrownieBase):
    def __init__(self, config, project):
        super().__init__(config, project)
        pytest.reverts = RevertContextManager

    def pytest_generate_tests(self, metafunc):
        # _session_isolation must always run first
        _make_fixture_execute_first(metafunc, "_session_isolation", "session")
        # module_isolation always runs before other module scoped functions
        _make_fixture_execute_first(metafunc, "module_isolation", "module")
        # fn_isolation always runs before other function scoped fixtures
        _make_fixture_execute_first(metafunc, "fn_isolation", "function")

    def pytest_collection_modifyitems(self, items):
        self._make_nodemap([i.nodeid for i in items])

        # determine which modules are properly isolated
        tests = {}
        for i in items:
            if "skip_coverage" in i.fixturenames and ARGV["coverage"]:
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

        if ARGV["update"]:
            isolated_tests = sorted(filter(self._check_updated, tests))
            # if update flag is active, add skip marker to unchanged tests
            for path in isolated_tests:
                tests[path][0].parent.add_marker("skip")
                self.isolated[path] = set(self.tests[path]["isolated"])

    def _check_updated(self, path):
        path = self._path(path)
        if path not in self.tests or not self.tests[path]["isolated"]:
            return False
        if ARGV["coverage"] and not self.tests[path]["coverage"]:
            return False
        for txhash in self.tests[path]["txhash"]:
            coverage._check_cached(txhash, False)
        return True

    def _make_nodemap(self, ids):
        self.node_map.clear()
        for item in ids:
            path, test = self._test_id(item)
            self.node_map.setdefault(path, []).append(test)

    def pytest_sessionstart(self):
        # remove PytestAssertRewriteWarning from terminalreporter warnings
        reporter = self.config.pluginmanager.get_plugin("terminalreporter")
        if "warnings" in reporter.stats:
            warnings = reporter.stats["warnings"]
            warnings = [i for i in warnings if "PytestAssertRewriteWarning" not in i.message]
            if not warnings:
                del reporter.stats["warnings"]
            else:
                reporter.stats["warnings"] = warnings

    # ensure each copy of ganache runs on a different port
    @pytest.fixture(scope="session", autouse=True)
    def _session_isolation(self, worker_id):
        key = ARGV["network"] or CONFIG["network"]["default"]
        if worker_id != "master":
            CONFIG["network"]["networks"][key]["test_rpc"]["port"] += int(worker_id[-1])
        network.connect(key)

    def pytest_runtest_protocol(self, item):
        # does not run on master
        path, test = self._test_id(item.nodeid)
        if path not in self.results:
            if path in self.tests and ARGV["update"]:
                self.results[path] = list(self.tests[path]["results"])
            else:
                self.results[path] = []

    def pytest_runtest_logreport(self, report):
        path, test_id = self._test_id(report.nodeid)
        if path in self.isolated:
            self.isolated[path].update(
                [i for i in _get_current_dependencies() if i in self.contracts]
            )
        idx = self.node_map[path].index(test_id)

        results = self.results[path]
        if report.when == "setup" and len(results) < idx + 1:
            results.append("s" if report.skipped else None)
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
        if not ARGV["coverage"] and (path in self.tests and self.tests[path]["coverage"]):
            txhash = self.tests[path]["txhash"]
        self.tests[path] = {
            "sha1": self._get_hash(path),
            "isolated": isolated,
            "coverage": ARGV["coverage"] or (path in self.tests and self.tests[path]["coverage"]),
            "txhash": txhash,
            "results": "".join(self.results[path]),
        }

    def pytest_sessionfinish(self):
        self._sessionfinish("build/tests.json")
        if ARGV["gas"]:
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
    def pytest_collection_modifyitems(self, items):
        # clear collection if isolation is not active
        if next((i for i in items if "module_isolation" not in i.fixturenames), False):
            items.clear()
            return True
        super().pytest_collection_modifyitems(items)

    def pytest_sessionfinish(self):
        self.tests = dict((k, v) for k, v in self.tests.items() if k in self.results)
        self._sessionfinish(f"build/tests-{self.config.workerinput['workerid']}.json")
