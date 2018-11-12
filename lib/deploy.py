#!/usr/bin/python3

import importlib
import os
import sys


if "--help" in sys.argv or len(sys.argv)<3 or sys.argv[2][:2]=="--":
    sys.exit("""Usage: brownie deploy <filename> [options]

Arguments:
  <filename>         The name of the deployment script to run

Options:
  --gas              Show gas costs for each successful transaction
  --network [name]   Use a specific network outlined in config.json (default development)
  --verbose          Verbose reporting
  --quiet            Minimal reporting

Use deploy to run scripts intended to deploy contracts onto the network.""")

name = sys.argv[2]

if not os.path.exists('deployments/{}.py'.format(name)):
    sys.exit("ERROR: Cannot find deployments/{}.py".format(name))

from lib.components.config import CONFIG
from lib.components.network import Network

module = importlib.import_module("deployments."+name)
Network(module).run(sys.argv[2])