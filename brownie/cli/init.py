#!/usr/bin/python3

from docopt import docopt
from pathlib import Path
import sys

import brownie.project as project
from brownie._config import ARGV, CONFIG


__doc__ = """Usage: brownie init [<path>] [options]

Arguments:
  <path>                Path to initialize (default is the current path)

Options:
  --force -f            Allow init inside a project subfolder
  --help -h             Display this message

brownie init is used to create new brownie projects. It creates the default
structure for the brownie environment:

build/                  Compiled contracts and test data
contracts/              Contract source code
reports/                Report files for contract analysis
scripts/                Scripts for deployment and interaction
tests/                  Scripts for project testing
brownie-config.json     Project configuration file"""


def main():
    args = docopt(__doc__)
    path = Path(args['<path>'] or '.').resolve()

    if CONFIG['folders']['brownie'] in str(path):
        sys.exit(
            "ERROR: Cannot init inside the main brownie installation folder.\n"
            "Create a new folder for your project and run brownie init there."
        )

    project.new(path, ARGV['force'])
    print("Brownie environment has been initiated at {}".format(path))
    sys.exit()
