#!/usr/bin/python3

from brownie import project
from brownie.utils import notify
from brownie.utils.docopt import docopt

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
interfaces/             Interface source code
reports/                Report files for contract analysis
scripts/                Scripts for deployment and interaction
tests/                  Scripts for project testing
brownie-config.yaml     Project configuration file"""


def main():
    args = docopt(__doc__)
    path = project.new(args["<path>"] or ".", args["--force"])
    notify("SUCCESS", f"Brownie environment has been initiated at {path}")
