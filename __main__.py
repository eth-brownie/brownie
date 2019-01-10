#!/usr/bin/python3

from docopt import docopt
import importlib
import os
import sys

import lib.init as init
from lib.components import config
CONFIG = config.CONFIG


__version__ = "0.9.0b"  # did you change this in docs/conf.py as well?


__doc__ = """Usage:  brownie [options] <command> [<args>...]

Commands:
  console            Load the console
  deploy             Run a script in the /deployments folder
  init               Initialize a new brownie project
  test               Run test scripts in the /tests folder

Options:
  --help             Display this message
  --network [name]   Use a specific network (default {})
  --verbose          Enable verbose reporting

Type 'brownie help <command>' for specific options and more information about
each command.""".format(CONFIG['default_network'])

print("Brownie v{} - Python development framework for Ethereum\n".format(__version__))
args = docopt(__doc__, options_first=True)

if args['<command>'] == "help" and args['<args>']:
    sys.argv[sys.argv.index('help')] = "--help"
    args['<command>'] = args['<args>'][0]

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

importlib.import_module("lib."+args['<command>']).main()