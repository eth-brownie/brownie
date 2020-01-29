#!/usr/bin/python3

import json
from hashlib import sha1

from py.path import local

from brownie._config import ARGV, CONFIG
from brownie.project.scripts import _get_ast_hash
from brownie.test import coverage, output

from .utils import convert_outcome


class PytestBrownieBase:
    def __init__(self, config, project):

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
            (k, v["bytecodeSha1"]) for k, v in project._build.items() if v["bytecode"]
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
            ARGV[key] = config.getoption("--coverage")
        ARGV["cli"] = "test"
        ARGV["gas"] = config.getoption("--gas")
        ARGV["revert"] = config.getoption("--revert-tb") or CONFIG["pytest"]["revert_traceback"]
        ARGV["update"] = config.getoption("--update")
        ARGV["network"] = None
        if config.getoption("--network"):
            ARGV["network"] = config.getoption("--network")[0]

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

    def pytest_report_teststatus(self, report):
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

    def _sessionfinish_coverage(self, coverage_eval):
        if ARGV["coverage"]:
            output._print_coverage_totals(self.project._build, coverage_eval)
            output._save_coverage_report(
                self.project._build, coverage_eval, self.project_path.joinpath("reports")
            )

    def pytest_keyboard_interrupt(self):
        ARGV["interrupt"] = True
