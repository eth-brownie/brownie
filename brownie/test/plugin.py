#!/usr/bin/python3

import sys
from pathlib import Path
from typing import Optional

import pytest

from brownie import project
from brownie._config import CONFIG, _modify_hypothesis_settings
from brownie.test.fixtures import PytestBrownieFixtures
from brownie.test.managers import PytestBrownieMaster, PytestBrownieRunner, PytestBrownieXdistRunner
from brownie.utils import color


def _get_project_path() -> Optional[Path]:
    key = next((i for i in sys.argv if i.startswith("--brownie-project")), "")
    if key == "--brownie-project":
        idx = sys.argv.index(key)
        project_path = Path(sys.argv[idx + 1]).absolute()
    elif key.startswith("--brownie-project="):
        project_path = Path(key[18:]).absolute()
    else:
        return project.check_for_project(".")

    if project_path != project.check_for_project(project_path):
        raise pytest.UsageError(f"Unable to load project at '{sys.argv[idx + 1]}'")
    return project_path


# set commandline options
def pytest_addoption(parser):
    parser.addoption(
        "--brownie-project", nargs=1, default=".", help="Load a brownie project at the given path"
    )

    if _get_project_path():
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
            "--failfast", action="store_true", help="Fail hypothesis tests quickly (no shrinking)"
        )
        parser.addoption(
            "--network",
            "-N",
            default=False,
            nargs=1,
            help=f"Use a specific network (default {CONFIG.settings['networks']['default']})",
        )
        parser.addoption(
            "--showinternal",
            action="store_true",
            help="Include Brownie internal frames in tracebacks",
        )


def pytest_load_initial_conftests(early_config):
    capsys = early_config.pluginmanager.get_plugin("capturemanager")

    project_path = _get_project_path()
    if project_path:
        # suspend stdout capture to display compilation data
        capsys.suspend()
        try:
            active_project = project.load(project_path)

            active_project.load_config()
            active_project._add_to_main_namespace()
        except Exception as e:
            # prevent pytest INTERNALERROR traceback when project fails to compile
            print(f"{color.format_tb(e)}\n")
            raise pytest.UsageError("Unable to load project")
        finally:
            capsys.resume()


def pytest_configure(config):
    if _get_project_path():

        if not config.getoption("showinternal"):
            # do not include brownie internals in tracebacks
            base_path = Path(sys.modules["brownie"].__file__).parent.as_posix()
            for module in [
                v
                for v in sys.modules.values()
                if getattr(v, "__file__", None) and v.__file__.startswith(base_path)
            ]:
                module.__tracebackhide__ = True
                module.__hypothesistracebackhide__ = True

        # enable verbose output if stdout capture is disabled
        if config.getoption("capture") == "no":
            config.option.verbose = True

        # if verbose mode is enabled, also enable hypothesis verbose mode
        if config.option.verbose:
            _modify_hypothesis_settings({"verbosity": 2}, "brownie-verbose")

        if config.getoption("numprocesses"):
            if config.getoption("interactive"):
                raise ValueError("Cannot use --interactive mode with xdist")
            Plugin = PytestBrownieMaster
        elif hasattr(config, "workerinput"):
            Plugin = PytestBrownieXdistRunner
        else:
            Plugin = PytestBrownieRunner

        if config.getoption("interactive"):
            config.option.failfast = True

        if config.getoption("failfast"):
            _modify_hypothesis_settings(
                {"phases": {"explicit": True, "generate": True, "target": True}}, "brownie-failfast"
            )

        active_project = project.get_loaded_projects()[0]
        session = Plugin(config, active_project)
        config.pluginmanager.register(session, "brownie-core")

        if not config.getoption("numprocesses"):
            fixtures = PytestBrownieFixtures(config, active_project)
            config.pluginmanager.register(fixtures, "brownie-fixtures")
