#!/usr/bin/python3

import sys
import time

if "--help" in sys.argv:
    sys.exit("""Usage: brownie console [options]

Connects to the network and opens the brownie console.""")

from lib.components import config
from lib.components.network import Network
from lib.services import console

network = Network(sys.modules[__name__])
print("Brownie environment is ready.")

console.run(globals(), config['folders']['project']+'/build/.history')
network.save()