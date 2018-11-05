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
  --verbose          Show full traceback when a deployment fails

Use deploy to run scripts intended to deploy contracts onto the network.""")

sys.path.insert(0, "")
name = sys.argv[2]


from lib.components.network import Network

network = Network()

contract = network.contract(sys.argv[2], sys.argv[3])
print(getattr(contract, sys.argv[4])(*sys.argv[5:sys.argv.index(next(i for i in sys.argv[5:] if '--' in i))]))