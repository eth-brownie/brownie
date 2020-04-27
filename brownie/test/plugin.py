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
            "--interactive",
            "-I",
            action="store_true",
            help="Open an interactive console each time a test fails",
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
            help=f"Use a specific network (default {CONFIG.settings['networks']['default']})",
        )


def pytest_configure(config):
    if project.check_for_project("."):

        active_project = project.load()
        active_project.load_config()
        active_project._add_to_main_namespace()

        # enable verbose output if stdout capture is disabled
        if config.getoption("capture") == "no":
            config.option.verbose = True

        if config.getoption("numprocesses"):
            if config.getoption("interactive"):
                raise ValueError("Cannot use --interactive mode with xdist")
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
