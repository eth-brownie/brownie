#!/usr/bin/python3

from docopt import docopt

from brownie.network import history
from brownie.test.main import run_tests
from brownie._config import ARGV, CONFIG


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
    if ARGV['coverage']:
        ARGV['always_transact'] = True
        history._revert_lock = True

    run_tests(
        CONFIG['folders']['project'],
        args['<filename>'],
        ARGV['update'],
        ARGV['coverage'],
        ARGV['gas']
    )
