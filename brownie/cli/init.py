#!/usr/bin/python3

from docopt import docopt
from pathlib import Path
import sys

import brownie.project as project
import brownie._config as config
CONFIG = config.CONFIG


__doc__ = """Usage: brownie init [<path>] [options]

Arguments:
  <path>                Path to initialize (default is the current path)

Options:
  --force -f            Allow init inside a project subfolder
  --help -h             Display this message

brownie init is used to create new brownie projects. It creates the default
structure for the brownie environment:

build/                  Compiled contracts and network data
contracts/              Solidity contracts
scripts/                Python scripts that are not for testing
tests/                  Python scripts for unit testing
brownie-config.json     Project configuration file"""


def main():
    args = docopt(__doc__)
    path = Path(args['<path>'] or '.').resolve()

    if CONFIG['folders']['brownie'] in str(path):
        sys.exit(
            "ERROR: Cannot init inside the main brownie installation folder.\n"
            "Create a new folder for your project and run brownie init there."
        )

    project.new(path, config.ARGV['force'])
    print("Brownie environment has been initiated at {}".format(path))
    sys.exit()
