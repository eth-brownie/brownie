#!/usr/bin/python3

import importlib
import os
import sys

__version__="0.1.0b"

folder = "{}/lib".format(__file__.rsplit('/', maxsplit=1)[0])
cmd = [i[:-3] for i in os.listdir(folder) if i[-3:]==".py"]
sys.path.insert(0, "")

print("Brownie v{} - Python development framework for Ethereum\n".format(__version__))

if len(sys.argv)<2 or sys.argv[1] not in cmd:
    sys.exit("""Usage:  brownie <command> [options]

Commands:
  console  Load the console
  deploy   Run a script in the /deployments folder
  init     Initialize a new brownie project
  test     Run test scripts in the /tests folder

Type brownie <command> --help for more information about a specific command.""")

import lib.init
importlib.import_module("lib."+sys.argv[1])