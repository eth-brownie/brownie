#!/usr/bin/python3

import json

import pytest
from xdist.scheduler import LoadFileScheduling

from brownie._config import CONFIG
from brownie.test import coverage

from .base import PytestBrownieBase


class PytestBrownieMaster(PytestBrownieBase):
    """
    Brownie plugin xdist master hooks.

    Hooks in this class are loaded by the master process when using xdist.
    """

    def pytest_xdist_make_scheduler(self, config, log):
        """
        Return a node scheduler implementation.

        Uses file scheduling to ensure consistent test execution with module-level
        isolation.
        """
        return LoadFileScheduling(config, log)

    def pytest_xdist_node_collection_finished(self, ids):
        """
        Called by the master node when a node finishes collecting.

        * Generates the node map
        * Populates `self.results` with previous test results. For tests that
          are executed by one of the runners, these results will be overwritten.
        """
        # required because pytest_collection_modifyitems is not called by master
        self._make_nodemap(ids)
        for path in self.node_map:
            if path in self.tests and CONFIG.argv["update"]:
                self.results[path] = list(self.tests[path]["results"])
            else:
                self.results[path] = ["s"] * len(self.node_map[path])

    def pytest_sessionfinish(self, session):
        """
        Called after whole test run finished, right before returning the exit
        status to the system.

        * Aggregates results from `build/tests-{workerid}.json` files and stores
          them as `build/test.json`.
        """
        if session.testscollected == 0:
            raise pytest.UsageError(
                "xdist workers failed to collect tests. Ensure all test cases are "
                "isolated with the module_isolation or fn_isolation fixtures.\n\n"
                "https://eth-brownie.readthedocs.io/en/stable/tests.html#isolating-tests"
            )
        build_path = self.project._build_path

        # aggregate worker test results
        report = {"tests": {}, "contracts": self.contracts, "tx": {}}
        for path in list(build_path.glob("tests-*.json")):
            with path.open() as fp:
                data = json.load(fp)
            assert data["contracts"] == report["contracts"]
            report["tests"].update(data["tests"])
            report["tx"].update(data["tx"])
            path.unlink()

        # store worker coverage results - these are used in `pytest_terminal_summary`
        for hash_, coverage_eval in report["tx"].items():
            coverage._add_transaction(hash_, coverage_eval)

        # save aggregate test results
        with build_path.joinpath("tests.json").open("w") as fp:
            json.dump(report, fp, indent=2, sort_keys=True, default=sorted)
