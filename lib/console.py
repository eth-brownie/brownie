#!/usr/bin/python3

import readline
import sys
import time
import traceback


if "--help" in sys.argv:
    sys.exit("""Usage: brownie console [options]

Connects to the network and opens the brownie console.""")

from lib.components import config
from lib.components.network import Network

network = Network(sys.modules[__name__])
print("Brownie environment is ready.")

try:
    readline.read_history_file(config['folders']['project']+'/build/.history')
except FileNotFoundError:
    pass

_multiline = False

while True:
    if not _multiline:
        try:
            cmd = input('>>> ')
        except KeyboardInterrupt:
            print("\nUse exit() or Ctrl-D (i.e. EOF) to exit.")
            continue
        except EOFError:
            print()
            cmd = "exit()"
        if cmd == "exit()":
            network.save()
            readline.remove_history_item(readline.get_current_history_length() - 1)
            readline.write_history_file(config['folders']['project']+'/build/.history')
            sys.exit()
        if not cmd.strip():
            continue
        if cmd.rstrip()[-1] == ":":
            _multiline = True
            continue
    else:
        try: 
            new_cmd = input('... ')
        except KeyboardInterrupt:
            print()
            _multiline = False
            continue
        if new_cmd: 
            cmd += '\n' + new_cmd
            continue
    if [i for i in ['{}', '[]', '()'] if cmd.count(i[0]) > cmd.count(i[1])]:
        _multiline = True
        continue
    _multiline = False
    _exec_result = None
    try:
        try: 
            exec('_exec_result = ' + cmd)
            if _exec_result != None:
                print(_exec_result)
        except SyntaxError:
            exec(cmd)    
    except:
        print("{}{}: {}".format(
                "".join(traceback.format_tb(sys.exc_info()[2])[1:]),
                sys.exc_info()[0].__name__, sys.exc_info()[1]))
