#!/usr/bin/python3

from docopt import docopt
import importlib
from pathlib import Path
import sys

from brownie import network
from brownie.cli.utils import color, notify
from brownie.exceptions import ProjectNotFound
from brownie._config import ARGV

__version__ = "1.0.0b10"  # did you change this in docs/conf.py as well?

__doc__ = """Usage:  brownie <command> [<args>...] [options <args>]

Commands:
  bake               Initialize from a brownie-mix template
  compile            Compiles the contract source files
  console            Load the console
  gui                Load the GUI to view opcodes and test coverage
  init               Initialize a new brownie project
  run                Run a script in the /scripts folder

Options:
  --help -h          Display this message

Type 'brownie <command> --help' for specific options and more information about
each command."""


def main():

    print(f"Brownie v{__version__} - Python development framework for Ethereum")

    # remove options before calling docopt
    if len(sys.argv) > 1 and sys.argv[1][0] != "-":
        idx = next((sys.argv.index(i) for i in sys.argv if i.startswith("-")), len(sys.argv))
        opts = sys.argv[idx:]
        sys.argv = sys.argv[:idx]
    args = docopt(__doc__)
    sys.argv += opts

    cmd_list = [i.stem for i in Path(__file__).parent.glob('[!_]*.py')]
    if args['<command>'] not in cmd_list:
        sys.exit("Invalid command. Try 'brownie --help' for available commands.")

    ARGV['cli'] = args['<command>']
    sys.modules['brownie'].a = network.accounts
    sys.modules['brownie'].__all__.append('a')

    try:
        importlib.import_module("brownie.cli."+args['<command>']).main()
    except ProjectNotFound:
        notify("ERROR", "Brownie environment has not been initiated for this folder.")
        print("Type 'brownie init' to create the file structure.")
    except Exception:
        print(color.format_tb(sys.exc_info()))
