#!/usr/bin/python3

import json
from hashlib import sha1
from pathlib import Path

import pytest
from xdist.scheduler import LoadFileScheduling

import brownie
from brownie._config import ARGV, CONFIG
from brownie.network.state import _get_current_dependencies
from brownie.project.scripts import _get_ast_hash
from brownie.test import coverage, output

STATUS_SYMBOLS = {"passed": ".", "skipped": "s", "failed": "F"}

STATUS_TYPES = {
    ".": "passed",
    "s": "skipped",
    "F": "failed",
    "E": "error",
    "x": "xfailed",
    "X": "xpassed",
}


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
        if exc_type is not brownie.exceptions.VirtualMachineError:
            raise exc_type(exc_value).with_traceback(traceback)
        if self.revert_msg is None or self.revert_msg == exc_value.revert_msg:
            return True
        raise AssertionError(
            f"Unexpected revert string '{exc_value.revert_msg}'\n{exc_value.source}"
        ) from None


class TestManager:
    def __init__(self, config, project):
        pytest.reverts = RevertContextManager

        self.config = config
        self.project = project
        self.project_path = project._path
        self.results = {}
        self.node_map = {}
        self.isolated = {}
        self._skip = {}
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
            if Path(k).exists() and self._get_hash(k) == v["sha1"]
        )
        build = self.project._build
        self.contracts = dict((k, v["bytecodeSha1"]) for k, v in build.items() if v["bytecode"])

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
        return Path(path).absolute().relative_to(self.project_path).as_posix()

    def _test_id(self, nodeid):
        path, test_id = nodeid.split("::")
        return self._path(path), test_id

    def _get_hash(self, path):
        hash_ = _get_ast_hash(path)
        for confpath in filter(lambda k: k in path, sorted(self.conf_hashes)):
            hash_ += self.conf_hashes[confpath]
        return sha1(hash_.encode()).hexdigest()

    def pytest_configure(self, config):
        for key in ("coverage", "always_transact"):
            ARGV[key] = config.getoption("--coverage")
        ARGV["gas"] = config.getoption("--gas")
        ARGV["revert"] = config.getoption("--revert-tb") or CONFIG["pytest"]["revert_traceback"]
        ARGV["update"] = config.getoption("--update")
        ARGV["network"] = None
        if config.getoption("--network"):
            ARGV["network"] = config.getoption("--network")[0]

    # plugin hooks

    def pytest_generate_tests(self, metafunc):
        # _session_isolation must always run first
        _make_fixture_execute_first(metafunc, "_session_isolation", "session")
        # module_isolation always runs before other module scoped functions
        _make_fixture_execute_first(metafunc, "module_isolation", "module")
        # fn_isolation always runs before other function scoped fixtures
        _make_fixture_execute_first(metafunc, "fn_isolation", "function")

    def pytest_collection_modifyitems(self, items):
        # does not run on master
        # if using xdist, clear collection if isolation is not active
        if hasattr(self.config, "workerinput"):
            if next((i for i in items if "module_isolation" not in i.fixturenames), False):
                items.clear()
                return True

        self._make_nodemap([i.nodeid for i in items])

        # determine which modules are properly isolated
        tests = {}
        for i in items:
            if "skip_coverage" in i.fixturenames and ARGV["coverage"]:
                i.add_marker("skip")
            path = i.parent.fspath
            if "module_isolation" not in i.fixturenames:
                tests[path] = None
                continue
            if path in tests and tests[path] is None:
                continue
            tests.setdefault(i.parent.fspath, []).append(i)
        isolated_tests = sorted(k for k, v in tests.items() if v)
        self.isolated = dict((self._path(i), set()) for i in isolated_tests)

        if ARGV["update"]:
            isolated_tests = sorted(filter(self._check_updated, tests))
            # if update flag is active, add skip marker to unchanged tests
            for path in isolated_tests:
                tests[path][0].parent.add_marker("skip")

    def _check_updated(self, path):
        path = self._path(path)
        if path not in self.tests or not self.tests[path]["isolated"]:
            return False
        if ARGV["coverage"] and not self.tests[path]["coverage"]:
            return False
        for txhash in self.tests[path]["txhash"]:
            coverage._check_cached(txhash, False)
        return True

    def pytest_xdist_make_scheduler(self, config, log):
        # if using xdist, schedule according to file
        return LoadFileScheduling(config, log)

    def pytest_xdist_node_collection_finished(self, ids):
        # required because pytest_collection_modifyitems is not called by master
        self._make_nodemap(ids)

    def _make_nodemap(self, ids):
        self.node_map.clear()
        for item in ids:
            path, test = self._test_id(item)
            self.node_map.setdefault(path, []).append(test)

        for path in self.node_map:
            if path in self.tests and ARGV["update"]:
                self.results[path] = list(self.tests[path]["results"])
            else:
                self.results[path] = []

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
        brownie.network.connect(key)

    def pytest_report_teststatus(self, report):
        if report.when == "setup":
            self._skip[report.nodeid] = report.skipped
            if report.failed:
                return "error", "E", "ERROR"
            return "", "", ""
        if report.when == "teardown":
            if report.failed:
                return "error", "E", "ERROR"
            elif self._skip[report.nodeid]:
                path, test_id = self._test_id(report.nodeid)
                idx = self.node_map[path].index(test_id)
                report.outcome = STATUS_TYPES[self.results[path][idx]]
                return "skipped", "s", "SKIPPED"
            return "", "", ""
        if hasattr(report, "wasxfail"):
            if report.skipped:
                return "xfailed", "x", "XFAIL"
            elif report.passed:
                return "xpassed", "X", "XPASS"
        return report.outcome, STATUS_SYMBOLS[report.outcome], report.outcome.upper()

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
            results[idx] = STATUS_SYMBOLS[report.outcome]
            if hasattr(report, "wasxfail"):
                results[idx] = "x" if report.skipped else "X"
        elif report.failed:
            results[idx] = "E"
        if report.when != "teardown" or idx < len(self.node_map[path]) - 1:
            return

        # TODO how to handle isolation data on xdist
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

    def pytest_sessionfinish(self, session):
        txhash = set(x for v in self.tests.values() for x in v["txhash"])
        coverage_eval = dict((k, v) for k, v in coverage.get_coverage_eval().items() if k in txhash)
        report = {"tests": self.tests, "contracts": self.contracts, "tx": coverage_eval}
        with self.project_path.joinpath("build/tests.json").open("w") as fp:
            json.dump(report, fp, indent=2, sort_keys=True, default=sorted)
        if ARGV["coverage"]:
            coverage_eval = brownie.test.coverage.get_merged_coverage_eval()
            output._print_coverage_totals(self.project._build, coverage_eval)
            output._save_coverage_report(
                self.project._build, coverage_eval, self.project._path.joinpath("reports")
            )
        if ARGV["gas"]:
            output._print_gas_profile()
        self.project.close(False)
        if session.testscollected == 0 and self.config.pluginmanager.get_plugin("dsession"):
            raise pytest.UsageError(
                "xdist workers failed to collect tests. Ensure all test cases are "
                "isolated with the module_isolation or fn_isolation fixtures.\n\n"
                "https://eth-brownie.readthedocs.io/en/stable/tests.html#isolating-tests"
            )

    def pytest_keyboard_interrupt(self):
        ARGV["interrupt"] = True
