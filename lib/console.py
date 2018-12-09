#!/usr/bin/python3

import readline
import sys
import time
import traceback


if "--help" in sys.argv:
    sys.exit("""Usage: brownie console [options]

Connects to the network and opens the brownie console.""")

from lib.components.network import Network
network = Network(sys.modules[__name__])
print("Brownie environment is ready.")

while True:
    cmd = input('>>> ')
    if cmd == "exit()":
        network.save()
        sys.exit()
    if not cmd: continue
    _exec_result = None
    cmd = "_exec_result = "+cmd
    try:
        exec(cmd)
        if _exec_result != None:
            print(_exec_result)
    except:
        print("{}{}: {}".format(
                ''.join(traceback.format_tb(sys.exc_info()[2])),
                sys.exc_info()[0].__name__, sys.exc_info()[1]))
