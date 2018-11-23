#!/usr/bin/python3

import readline
import sys
import time
import traceback


if "--help" in sys.argv:
    sys.exit("""Usage: brownie console [options]

Options:
  --gas              Show gas costs for each successful transaction
  --network [name]   Use a specific network outlined in config.json (default development)

TODO - Write some stuff here""")

from lib.components.network import Network
Network(sys.modules[__name__])

while True:
    cmd = input('>>> ')
    if cmd == "exit()": sys.exit()
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
