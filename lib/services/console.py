#!/usr/bin/python3

import builtins
import readline
import sys
import json
from threading import Lock
import traceback

BLUE = "\x1b[36m"
YELLOW = "\x1b[33m"
DEFAULT = "\x1b[0m"


class Console:

    def __init__(self):
        self._print_lock = Lock()
        self._multiline = False
        self._prompt = ">>> "

    def _print(self, *args, sep=' ', end='\n', file=sys.stdout, flush=False):
        with self._print_lock:
            ln = readline.get_line_buffer()
            file.write('\r'+' '*(len(ln)+4)+'\r')
            file.write(sep.join(str(i) for i in args)+end)
            file.write(self._prompt+ln)
            file.flush()
            

    def run(self, globals_dict, history_file = None):
        builtins.print = self._print
        local_ = {}
        globals_dict['dir'] = _brownie_dir
        if history_file:
            try:
                readline.read_history_file(history_file)
            except FileNotFoundError:
                pass
        while True:
            if not self._multiline:
                try:
                    cmd = input(self._prompt)
                except KeyboardInterrupt:
                    sys.stdout.write("\nUse exit() or Ctrl-D (i.e. EOF) to exit.\n")
                    sys.stdout.flush()
                    continue
                except EOFError:
                    print()
                    cmd = "exit()"
                if cmd == "exit()":
                    if history_file:
                        readline.remove_history_item(readline.get_current_history_length() - 1)
                        readline.write_history_file(history_file)
                    return
                if not cmd.strip():
                    continue
                if cmd.rstrip()[-1] == ":":
                    self._multiline = True
                    self._prompt = "... "
                    continue
            else:
                try: 
                    new_cmd = input('... ')
                except KeyboardInterrupt:
                    print()
                    self._multiline = False
                    self._prompt = ">>> "
                    continue
                if new_cmd: 
                    cmd += '\n' + new_cmd
                    continue
            if [i for i in ['{}', '[]', '()'] if cmd.count(i[0]) > cmd.count(i[1])]:
                self._multiline = True
                continue
            self._multiline = False
            self._prompt = ""
            try:
                try: 
                    local_['_result'] = None
                    exec('_result = ' + cmd, globals_dict, local_)
                    if local_['_result'] != None:
                        r = local_['_result']
                        if type(r) is dict or (
                            type(r) is list and 
                            len(r) == len([i for i in r if type(i) is dict])
                        ):
                            print(json.dumps(
                                r,
                                default=str,
                                indent=4,
                                sort_keys=True
                            ))
                        else:
                            print(local_['_result'])
                except SyntaxError:
                    exec(cmd, globals_dict, local_)
            except:
                print("{}{}: {}".format(
                        "".join(traceback.format_tb(sys.exc_info()[2])[1:]),
                        sys.exc_info()[0].__name__, sys.exc_info()[1]))
            self._prompt = ">>> "


def _brownie_dir(obj=None):
    if not obj:
        obj = sys.modules[__name__]
    results = [(i,getattr(obj,i)) for i in builtins.dir(obj) if i[0]!="_"]
    print("["+"{}, ".format(DEFAULT).join("{}{}".format(
        BLUE if callable(i[1]) else YELLOW, i[0]
    ) for i in results)+DEFAULT+"]")
    

sys.modules[__name__] = Console()