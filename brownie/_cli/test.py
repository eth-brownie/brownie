#!/usr/bin/python3

import sys

import pytest

from brownie import project
from brownie._config import CONFIG, _load_project_structure_config
from brownie.exceptions import ProjectNotFound
from brownie.utils.docopt import docopt

__doc__ = f"""Usage: brownie test [<path>, ...] [options]

Arguments:
  [<path>, ...]            Path(s) of the test modules to run

Brownie Options:
  --update -U              Only run tests where changes have occurred
  --coverage -C            Evaluate contract test coverage
  --interactive -I         Open an interactive console each time a test fails
  --stateful [true,false]  Only run stateful tests, or skip them
  --failfast               Fail hypothesis tests quickly (no shrinking)
  --revert-tb -R           Show detailed traceback on unhandled transaction reverts
  --gas -G                 Display gas profile for function calls
  --network [name]         Use a specific network (default {CONFIG.settings['networks']['default']})
  --showinternal           Include Brownie internal frames in tracebacks

Pytest Options:
  -s                       Disable stdout capture when running tests
  -n [numprocesses]        Number of workers to use for xdist distributed testing,
                           set to 'auto' for automatic detection of number of CPUs
  --durations [num]        show slowest setup/test durations (num=0 for all)
  --exitfirst -x           Exit instantly on first error or failed test
  --verbose -v             Increase verbosity
  --disable-warnings -w    Disable all warnings

Help Options:
  --fixtures            Show a list of available fixtures
  --help -h             Display this message

Launches pytest and runs the tests for a project."""


def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        # display the help screen and exit
        docopt(__doc__)

    project_path = project.check_for_project(".")
    if project_path is None:
        raise ProjectNotFound

    # ensure imports are possible from anywhere in the project
    project.main._add_to_sys_path(project_path)

    pytest_args = sys.argv[sys.argv.index("test") + 1 :]
    if not pytest_args or pytest_args[0].startswith("-"):
        structure_config = _load_project_structure_config(project_path)
        pytest_args.insert(0, project_path.joinpath(structure_config["tests"]).as_posix())

    return_code = pytest.main(pytest_args, ["pytest-brownie"])

    if return_code:
        # only exit with non-zero status to make testing easier
        sys.exit(return_code)
