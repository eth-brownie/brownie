#!/usr/bin/python3

import sys

import brownie
from brownie._config import CONFIG
from brownie.test._manager import TestManager
from brownie.test.fixtures import TestFixtures


# set commandline options
def pytest_addoption(parser):
    if brownie.project.check_for_project("."):
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
            "--network",
            "-N",
            default=False,
            nargs=1,
            help=f"Use a specific network (default {CONFIG['network']['default']})",
        )


def pytest_configure(config):
    if brownie.project.check_for_project("."):

        # load project and generate dynamic fixtures
        project = brownie.project.load()
        project.load_config()

        session = TestManager(config, project)
        config.pluginmanager.register(session, "brownie-core")
        fixtures = TestFixtures(config, project)
        config.pluginmanager.register(fixtures, "brownie-fixtures")

        # by default, suppress stdout on failed tests
        if not next((i for i in sys.argv if i.startswith("--show-capture=")), False):
            config.option.showcapture = "no"
