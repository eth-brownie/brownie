#!/usr/bin/python3

from docopt import docopt
import importlib
from pathlib import Path
import sys

from brownie.cli.utils import color
import brownie.project as project

__version__ = "0.9.6"  # did you change this in docs/conf.py as well?


__doc__ = """Usage:  brownie <command> [<args>...] [options <args>]

Commands:
  init               Initialize a new brownie project
  console            Load the console
  run                Run a script in the /scripts folder
  test               Run test scripts in the /tests folder
  coverage           Evaluate test coverage

Options:
  -h --help          Display this message

Type 'brownie <command> --help' for specific options and more information about
each command."""

print("Brownie v{} - Python development framework for Ethereum\n".format(__version__))

if len(sys.argv)>1 and sys.argv[1][0] != "-":
    try:
        idx = next(sys.argv.index(i) for i in sys.argv if i[0]=="-")
        opts = sys.argv[idx:]
        sys.argv = sys.argv[:idx]
    except StopIteration:
        opts = []

args = docopt(__doc__)
sys.argv += opts


cmd_list = [i.name[:-3] for i in Path(__file__).parent.glob('*.py') if i.name[0]!="_"]
if args['<command>'] not in cmd_list:
    sys.exit("Invalid command. Try 'brownie --help' for available commands.")

if args['<command>'] != "init":
    path = project.check_for_project('.')
    if not path:
        sys.exit(
            "ERROR: Brownie environment has not been initiated for this folder."
            "\nType 'brownie init' to create the file structure."
        )
    project.load(path)

try:
    importlib.import_module("brownie.cli."+args['<command>']).main()
except Exception:
    print(color.format_tb(sys.exc_info()))