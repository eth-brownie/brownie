#!/usr/bin/python3

import importlib
import sys
from pathlib import Path

from brownie import network
from brownie._config import ARGV
from brownie.exceptions import ProjectNotFound
from brownie.utils import color, notify
from brownie.utils.docopt import docopt, levenshtein_norm

__version__ = "1.6.4"

__doc__ = """Usage:  brownie <command> [<args>...] [options <args>]

Commands:
  init               Initialize a new brownie project
  bake               Initialize from a brownie-mix template
  ethpm              Commands related to the ethPM package manager
  compile            Compiles the contract source files
  console            Load the console
  test               Run test cases in the tests/ folder
  run                Run a script in the scripts/ folder
  accounts           Manage local accounts
  gui                Load the GUI to view opcodes and test coverage
  analyze            Find security vulnerabilities using the MythX API

Options:
  --help -h          Display this message

Type 'brownie <command> --help' for specific options and more information about
each command."""


def main():

    print(f"Brownie v{__version__} - Python development framework for Ethereum\n")

    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        # this call triggers a SystemExit
        docopt(__doc__, ["brownie", "-h"])

    cmd = sys.argv[1]
    cmd_list = [i.stem for i in Path(__file__).parent.glob("[!_]*.py")]
    if cmd not in cmd_list:
        distances = sorted([(i, levenshtein_norm(cmd, i)) for i in cmd_list], key=lambda k: k[1])
        if distances[0][1] <= 0.2:
            sys.exit(f"Invalid command. Did you mean 'brownie {distances[0][0]}'?")
        sys.exit("Invalid command. Try 'brownie --help' for available commands.")

    ARGV["cli"] = cmd
    sys.modules["brownie"].a = network.accounts
    sys.modules["brownie"].__all__.append("a")

    try:
        importlib.import_module(f"brownie._cli.{cmd}").main()
    except ProjectNotFound:
        notify("ERROR", "Brownie environment has not been initiated for this folder.")
        print("Type 'brownie init' to create the file structure.")
    except Exception as e:
        print(color.format_tb(e))
