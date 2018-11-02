#!/usr/bin/python3

import importlib
import json
import os
import solc
from subprocess import Popen, DEVNULL
import sys
from web3 import Web3, HTTPProvider

cmd = [i[:-3] for i in os.listdir(__file__.rsplit('/',maxsplit = 1)[0]+'/lib') if i[-3:] == ".py"]

if len(sys.argv)>1 and sys.argv[1] in cmd:
    importlib.import_module("lib."+sys.argv[1])
else:
    print("""Brownie 0.0.1 - python based development framework for Ethereum
    
Usage:  brownie <command> [options]

Commands:
  init     Initialize a new brownie project.
  test     Run python tests in /tests folder.""")

sys.exit()