#!/usr/bin/python3

import importlib
import os
import sys

from lib.components import config

__version__="0.9.0b"  # did you change this in docs/conf.py as well?

cmd = [i[:-3] for i in os.listdir(config['folders']['brownie']+"/lib") if i[-3:]==".py"]
sys.path.insert(0, config['folders']['project'])

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