#!/usr/bin/python3

import importlib
import sys
from pathlib import Path

from brownie import network
from brownie._config import CONFIG, __version__
from brownie.exceptions import ProjectNotFound
from brownie.utils import color, notify
from brownie.utils.docopt import docopt, levenshtein_norm

__doc__ = """Usage:  brownie <command> [<args>...] [options <args>]

Commands:
  init               Initialize a new brownie project
  bake               Initialize from a brownie-mix template
  pm                 Install and manage external packages
  compile            Compile the contract source files
  console            Load the console
  test               Run test cases in the tests/ folder
  run                Run a script in the scripts/ folder
  accounts           Manage local accounts
  networks           Manage network settings
  gui                Load the GUI to view opcodes and test coverage

Options:
  --help -h          Display this message
  --version          Show version and exit

Type 'brownie <command> --help' for specific options and more information about
each command."""


def main():
    print(f"Brownie v{__version__} - Python development framework for Ethereum\n")

    if "--version" in sys.argv:
        sys.exit()

    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        # this call triggers a SystemExit
        docopt(__doc__, ["brownie", "-h"])

    if "-i" in sys.argv:
        # a small kindness to ipython users
        sys.argv[sys.argv.index("-i")] = "-I"

    cmd = sys.argv[1]
    cmd_list = [i.stem for i in Path(__file__).parent.glob("[!_]*.py")]
    if cmd not in cmd_list:
        distances = sorted([(i, levenshtein_norm(cmd, i)) for i in cmd_list], key=lambda k: k[1])
        if distances[0][1] <= 0.2:
            sys.exit(f"Invalid command. Did you mean 'brownie {distances[0][0]}'?")
        sys.exit("Invalid command. Try 'brownie --help' for available commands.")

    CONFIG.argv["cli"] = cmd
    sys.modules["brownie"].a = network.accounts
    sys.modules["brownie"].__all__.append("a")

    try:
        importlib.import_module(f"brownie._cli.{cmd}").main()
    except ProjectNotFound:
        notify("ERROR", "Brownie environment has not been initiated for this folder.")
        sys.exit("Type 'brownie init' to create the file structure.")
    except Exception as e:
        if "-r" in sys.argv:
            raise e
        else:
            sys.exit(color.format_tb(e))
