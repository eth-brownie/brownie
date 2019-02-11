#!/usr/bin/python3

from docopt import docopt
import importlib
import os
import sys

import lib.init as init
from lib.services import config, color
CONFIG = config.CONFIG


__version__ = "0.9.0b"  # did you change this in docs/conf.py as well?

__doc__ = """Usage:  brownie <command> [<args>...] [options <args>]

Commands:
  init               Initialize a new brownie project
  console            Load the console
  run                Run a script in the /scripts folder
  test               Run test scripts in the /tests folder
  coverage           Evaluate test coverage

Options:
  -h --help          Display this message
  --network <name>   Use a specific network (default {})
  --verbose          Enable verbose reporting

Type 'brownie <command> --help' for specific options and more information about
each command.""".format(CONFIG['network_defaults']['name'])

if len(sys.argv)>1 and sys.argv[1][0] != "-":
    try:
        idx = next(sys.argv.index(i) for i in sys.argv if i[0]=="-")
        opts = sys.argv[idx:]
        sys.argv = sys.argv[:idx]
    except StopIteration:
        opts = []

print("Brownie v{} - Python development framework for Ethereum\n".format(__version__))
args = docopt(__doc__)
sys.argv += opts

lib_folder = __file__[:__file__.rfind('/')]+"/lib"
cmd_list = [i[:-3] for i in os.listdir(lib_folder) if i[-3:]==".py"]
if args['<command>'] not in cmd_list:
    sys.exit("Invalid command. Try 'brownie --help' for available commands.")

if args['<command>'] != "init":
    if not init.check_for_project():
        sys.exit(
            "ERROR: Brownie environment has not been initiated for this folder."
            "\nType 'brownie init' to create the file structure."
        )
    init.create_build_folders()

try:
    importlib.import_module("lib."+args['<command>']).main()
except Exception:
    print(color.format_tb(sys.exc_info()))