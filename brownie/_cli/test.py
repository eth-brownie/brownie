#!/usr/bin/python3

import pytest
from docopt import docopt

from brownie import project
from brownie._config import CONFIG
from brownie.exceptions import ProjectNotFound

__doc__ = f"""Usage: brownie test [<path>] [options]

Arguments:
  [<path>]                   Path to the test(s) to run.

Options:
  --coverage -C              Evaluate contract test coverage
  --gas -G                   Display gas profile for function calls
  --network [name]           Use a specific network (default {CONFIG['network']['default']})
  --revert-tb -R             Show detailed traceback on tx reverts
  --update -U                Only run tests where changes have occurred
  --help -h                  Display this message

Plugin Options:
  -n [numprocesses]          Number of workers to use for xdist distributed testing,
                             set to 'auto' for automatic detection of number of CPUs

Launches pytest and runs the project tests."""


def main():
    args = docopt(__doc__)

    project_path = project.check_for_project(".")
    if project_path is None:
        raise ProjectNotFound

    if args["<path>"] is None:
        args["<path>"] = project_path.joinpath("tests").as_posix()

    pytest_args = [args["<path>"]]
    for opt, value in [(k, v) for k, v in args.items() if k.startswith("-") and v]:
        if value is True:
            pytest_args.append(opt)
        elif isinstance(value, str):
            pytest_args.extend([opt, value])

    pytest.main(pytest_args, ["pytest-brownie"])
