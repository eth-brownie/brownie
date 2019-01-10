#!/usr/bin/python3

from docopt import docopt
import sys
import time

from lib.components.network import Network
from lib.services import console

from lib.components import config
CONFIG = config.CONFIG


__doc__ = """Usage: brownie [options] console

Options:
  --help             Display this message
  --network [name]   Use a specific network (default {})
  --verbose          Enable verbose reporting

Connects to the network and opens the brownie console.
""".format(CONFIG['default_network'])

def main():
    args = docopt(__doc__, options_first=True)

    network = Network(sys.modules[__name__])
    print("Brownie environment is ready.")

    console.run(globals(), "build/.history")
    network.save()