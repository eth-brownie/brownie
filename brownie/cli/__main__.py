#!/usr/bin/python3

from docopt import docopt
import importlib
from pathlib import Path
import sys

import brownie
from brownie.cli.utils import color
import brownie.project as project

__version__ = "1.0.0b5"  # did you change this in docs/conf.py as well?

__doc__ = """Usage:  brownie <command> [<args>...] [options <args>]

Commands:
  bake               Initialize from a brownie-mix template
  compile            Compiles the contract source files
  console            Load the console
  gui                Load the GUI to view opcodes and test coverage
  init               Initialize a new brownie project
  run                Run a script in the /scripts folder
  test               Run test scripts in the /tests folder

Options:
  --help -h          Display this message

Type 'brownie <command> --help' for specific options and more information about
each command."""


def main():

    print("Brownie v{} - Python development framework for Ethereum\n".format(__version__))

    if len(sys.argv) > 1 and sys.argv[1][0] != "-":
        try:
            idx = next(sys.argv.index(i) for i in sys.argv if i[0] == "-")
            opts = sys.argv[idx:]
            sys.argv = sys.argv[:idx]
        except StopIteration:
            opts = []

    args = docopt(__doc__)
    sys.argv += opts

    cmd_list = [i.stem for i in Path(__file__).parent.glob('[!_]*.py')]
    if args['<command>'] not in cmd_list:
        sys.exit("Invalid command. Try 'brownie --help' for available commands.")

    if args['<command>'] not in ("init", "bake"):
        path = project.check_for_project('.')
        if not path:
            sys.exit(
                "ERROR: Brownie environment has not been initiated for this folder."
                "\nType 'brownie init' to create the file structure."
            )
        if args['<command>'] != "compile" and "--help" not in opts:
            for container in project.load(path):
                setattr(brownie, container._name, container)
                brownie.__all__.append(container._name)
            brownie.a = brownie.accounts
            brownie.__all__.append('a')

    try:
        importlib.import_module("brownie.cli."+args['<command>']).main()
    except Exception:
        print(color.format_tb(sys.exc_info()))
