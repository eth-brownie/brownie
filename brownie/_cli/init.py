#!/usr/bin/python3

from brownie import project
from brownie.utils import notify
from brownie.utils.docopt import docopt

__doc__ = """Usage: brownie init [<path>] [options]

Arguments:
  <path>                Path to initialize (default is the current path)

Options:
  --force -f            Allow initialization inside a directory that is not
                        empty, or a subdirectory of an existing project
  --help -h             Display this message

brownie init is used to create new brownie projects. It creates the default
structure for the brownie environment:

build/                  Compiled contracts and test data
contracts/              Contract source code
interfaces/             Interface source code
reports/                Report files for contract analysis
scripts/                Scripts for deployment and interaction
tests/                  Scripts for project testing
"""


def main():
    args = docopt(__doc__)
    path = project.new(args["<path>"] or ".", args["--force"], args["--force"])
    notify("SUCCESS", f"A new Brownie project has been initialized at {path}")
