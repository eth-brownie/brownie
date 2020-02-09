#!/usr/bin/python3

from brownie import project
from brownie._config import CONFIG
from brownie.test.fixtures import PytestBrownieFixtures
from brownie.test.managers import PytestBrownieMaster, PytestBrownieRunner, PytestBrownieXdistRunner


# set commandline options
def pytest_addoption(parser):
    if project.check_for_project("."):
        parser.addoption(
            "--coverage", "-C", action="store_true", help="Evaluate contract test coverage"
        )
        parser.addoption(
            "--gas", "-G", action="store_true", help="Display gas profile for function calls"
        )
        parser.addoption(
            "--update", "-U", action="store_true", help="Only run tests where changes have occurred"
        )
        parser.addoption(
            "--revert-tb", "-R", action="store_true", help="Show detailed traceback on tx reverts"
        )
        parser.addoption(
            "--stateful",
            choices=["true", "false"],
            default=None,
            help="Only run or skip stateful tests (default: run all tests)",
        )
        parser.addoption(
            "--network",
            "-N",
            default=False,
            nargs=1,
            help=f"Use a specific network (default {CONFIG['network']['default']})",
        )


def pytest_configure(config):
    if project.check_for_project("."):

        active_project = project.load()
        active_project.load_config()
        active_project._add_to_main_namespace()

        if config.getoption("numprocesses"):
            Plugin = PytestBrownieMaster
        elif hasattr(config, "workerinput"):
            Plugin = PytestBrownieXdistRunner
        else:
            Plugin = PytestBrownieRunner

        session = Plugin(config, active_project)
        config.pluginmanager.register(session, "brownie-core")

        if not config.getoption("numprocesses"):
            fixtures = PytestBrownieFixtures(config, active_project)
            config.pluginmanager.register(fixtures, "brownie-fixtures")
