#!/usr/bin/python3

import builtins
from docopt import docopt
import readline
import sys
from threading import Lock
import time

from lib.components.network import Network
from lib.components.contract import _ContractBase, _ContractMethod
from lib.services import color, config
CONFIG = config.CONFIG


__doc__ = """Usage: brownie console [options]

Options:
  -h --help             Display this message
  -n --network <name>   Use a specific network (default {})
  --verbose          Enable verbose reporting

Connects to the network and opens the brownie console.
""".format(CONFIG['network_defaults']['name'])


REMOVE = [
    'Network',
    'Console',
    'docopt'
    'main',
    'sys',
    'CONFIG',
    'Lock',
    'REMOVE',
    'builtins',
    'readline'
]


class Console:

    def __init__(self):
        self._print_lock = Lock()
        self._multiline = False
        self._prompt = ">>> "
        builtins.print = self._print
        local_ = {}
        self.__dict__.update(dict((k,v) for k,v in globals().items() if k[0]!="_" and k not in REMOVE))
        self.__dict__['dir'] = self._dir
        try:
            readline.read_history_file("build/.history")
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
                    readline.remove_history_item(readline.get_current_history_length() - 1)
                    readline.write_history_file("build/.history")
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
                    exec('_result = ' + cmd, self.__dict__, local_)
                    if local_['_result'] != None:
                        r = local_['_result']
                        if type(r) is dict or (
                            type(r) is list and 
                            len(r) == len([i for i in r if type(i) is dict])
                        ):
                            color.json(r)
                        else:
                            print(local_['_result'])
                except SyntaxError:
                    exec(cmd, self.__dict__, local_)
            except:
                print(color.format_tb(sys.exc_info(), start=1))
            self._prompt = ">>> "

    def _print(self, *args, sep=' ', end='\n', file=sys.stdout, flush=False):
        with self._print_lock:
            ln = readline.get_line_buffer()
            file.write('\r'+' '*(len(ln)+4)+'\r')
            file.write(sep.join(str(i) for i in args)+end)
            file.write(self._prompt+ln)
            file.flush()

    def _dir(self, obj=None):
        if obj is None:
            obj = self
        results = [(i,getattr(obj,i)) for i in builtins.dir(obj) if i[0]!="_"]
        print("["+"{}, ".format(color()).join(
            _dir_color(i[1])+i[0] for i in results
        )+color()+"]")

def _dir_color(obj):
    if type(obj).__name__ == "module":
        return color(CONFIG['colors']['module'])
    try:
        if issubclass(type(obj), _ContractBase):
            return color(CONFIG['colors']['contract'])
        if issubclass(type(obj), _ContractMethod):
            return color(CONFIG['colors']['contract_method'])
    except TypeError:
        pass
    if not callable(obj):
        return color(CONFIG['colors']['value'])
    return color(CONFIG['colors']['callable'])

def main():
    args = docopt(__doc__)

    network = Network(sys.modules[__name__])
    print("Brownie environment is ready.")

    Console()
    network.save()