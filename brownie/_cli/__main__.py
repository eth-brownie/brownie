#!/usr/bin/python3

import importlib
import sys
from pathlib import Path

from docopt import docopt

from brownie import network
from brownie._config import ARGV
from brownie.exceptions import ProjectNotFound
from brownie.utils import color, notify

__version__ = "1.3.1"

__doc__ = """Usage:  brownie <command> [<args>...] [options <args>]

Commands:
  bake               Initialize from a brownie-mix template
  compile            Compiles the contract source files
  console            Load the console
  ethpm              Commands related to the ethPM package manager
  gui                Load the GUI to view opcodes and test coverage
  init               Initialize a new brownie project
  run                Run a script in the /scripts folder
  analyze            Find security vulnerabilities using the MythX API

Options:
  --help -h          Display this message

Type 'brownie <command> --help' for specific options and more information about
each command."""


def main():

    print(f"Brownie v{__version__} - Python development framework for Ethereum\n")

    # remove options before calling docopt
    if len(sys.argv) > 1 and sys.argv[1][0] != "-":
        idx = next((sys.argv.index(i) for i in sys.argv if i.startswith("-")), len(sys.argv))
        opts = sys.argv[idx:]
        sys.argv = sys.argv[:idx]
    args = docopt(__doc__)
    sys.argv += opts

    cmd_list = [i.stem for i in Path(__file__).parent.glob("[!_]*.py")]
    if args["<command>"] not in cmd_list:
        sys.exit("Invalid command. Try 'brownie --help' for available commands.")

    ARGV["cli"] = args["<command>"]
    sys.modules["brownie"].a = network.accounts
    sys.modules["brownie"].__all__.append("a")

    try:
        importlib.import_module(f"brownie._cli.{args['<command>']}").main()
    except ProjectNotFound:
        notify("ERROR", "Brownie environment has not been initiated for this folder.")
        print("Type 'brownie init' to create the file structure.")
    except Exception as e:
        print(color.format_tb(e))
