#!/usr/bin/python3

from docopt import docopt

from brownie import project
from brownie.test.main import run_tests
from brownie._config import ARGV

__doc__ = """Usage: brownie test [<filename>] [options]

Arguments:
  <filename>              Only run tests from a specific file or folder

Options:

  --update -u             Only run tests where changes have occurred
  --coverage -c           Evaluate test coverage
  --gas -g                Display gas profile for function calls
  --verbose -v            Enable verbose reporting
  --tb -t                 Show entire python traceback on exceptions
  --help -h               Display this message

By default brownie runs every script found in the tests folder as well as any
subfolders. Files and folders beginning with an underscore will be skipped."""


def main():
    args = docopt(__doc__)
    ARGV._update_from_args(args)

    project.load()
    run_tests(
        args['<filename>'],
        ARGV['update'],
        ARGV['coverage'],
        ARGV['gas']
    )
