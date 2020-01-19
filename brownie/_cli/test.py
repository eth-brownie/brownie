#!/usr/bin/python3

import pytest
from docopt import docopt

from brownie import project
from brownie._config import CONFIG
from brownie.exceptions import ProjectNotFound

__doc__ = f"""Usage: brownie test [<path>] [options]

Arguments:
  [<path>]              Path to the test(s) to run

Brownie Options:
  --update -U           Only run tests where changes have occurred
  --coverage -C         Evaluate contract test coverage
  --revert-tb -R        Show detailed traceback on unhandled transaction reverts
  --gas -G              Display gas profile for function calls
  --network [name]      Use a specific network (default {CONFIG['network']['default']})

Pytest Options:
  -n [numprocesses]     Number of workers to use for xdist distributed testing,
                        set to 'auto' for automatic detection of number of CPUs
  --durations [num]     show slowest setup/test durations (num=0 for all)
  --exitfirst -x        Exit instantly on first error or failed test
  --verbose -v          Increase verbosity

Help Options:
  --fixtures            Show a list of available fixtures
  --help -h             Display this message

Launches pytest and runs the tests for a project."""


def main():
    args = docopt(__doc__)

    project_path = project.check_for_project(".")
    if project_path is None:
        raise ProjectNotFound

    if args["<path>"] is None:
        args["<path>"] = project_path.joinpath("tests").as_posix()

    pytest_args = [args["<path>"]]
    for opt, value in [(i, args[i]) for i in sorted(args) if i.startswith("-") and args[i]]:
        if value is True:
            pytest_args.append(opt)
        elif isinstance(value, str):
            pytest_args.extend([opt, value])

    pytest.main(pytest_args, ["pytest-brownie"])
