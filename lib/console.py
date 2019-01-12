#!/usr/bin/python3

from docopt import docopt
import sys
import time

from lib.components.network import Network
from lib.services import console

from lib.components import config
CONFIG = config.CONFIG


__doc__ = """Usage: brownie console [options]

Options:
  -h --help             Display this message
  -n --network <name>   Use a specific network (default {})
  --verbose          Enable verbose reporting

Connects to the network and opens the brownie console.
""".format(CONFIG['network_defaults']['name'])

def main():
    args = docopt(__doc__)

    network = Network(sys.modules[__name__])
    print("Brownie environment is ready.")

    console.run(globals(), "build/.history")
    network.save()