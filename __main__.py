#!/usr/bin/python3

import importlib
import os
import sys

from lib.components.config import BROWNIE_FOLDER, CONFIG

__version__="0.1.0b"

cmd = [i[:-3] for i in os.listdir(BROWNIE_FOLDER+"/lib") if i[-3:]==".py"]
sys.path.insert(0, "")

print("Brownie v{} - Python development framework for Ethereum\n".format(__version__))

if len(sys.argv)<2 or sys.argv[1] not in cmd:
    sys.exit("""Usage:  brownie <command> [options]

Commands:
  console  Load the console
  deploy   Run a script in the /deployments folder
  init     Initialize a new brownie project
  test     Run test scripts in the /tests folder

Options:
  --network [name]   Use a specific network (default {})
  --verbose          Enable verbose reporting

Type brownie <command> --help for specific options and more information about
each command.""".format(CONFIG['default_network']))

import lib.init
importlib.import_module("lib."+sys.argv[1])