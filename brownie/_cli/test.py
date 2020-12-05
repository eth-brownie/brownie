import sys

import click
import pytest

from brownie import project
from brownie.exceptions import ProjectNotFound


@click.command(
    short_help="Run test cases in the `tests/` folder",
    context_settings=dict(ignore_unknown_options=True),
)
@click.argument("pytest_args", nargs=-1, type=click.UNPROCESSED)
def cli(pytest_args):
    """Usage: brownie test [<path>, ...] [options]

Arguments:
  [<path>, ...]            Path(s) of the test modules to run

Brownie Options:
  --update -U              Only run tests where changes have occurred
  --coverage -C            Evaluate contract test coverage
  --stateful [true,false]  Only run stateful tests, or skip them
  --failfast               Fail hypothesis tests quickly (no shrinking)
  --revert-tb -R           Show detailed traceback on unhandled transaction reverts

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

    project_path = project.check_for_project(".")
    if project_path is None:
        raise ProjectNotFound

    # ensure imports are possible from anywhere in the project
    project.main._add_to_sys_path(project_path)

    return_code = pytest.main([*pytest_args], ["pytest-brownie"])

    if return_code:
        # only exit with non-zero status to make testing easier
        sys.exit(return_code)
