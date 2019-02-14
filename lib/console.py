#!/usr/bin/python3

import builtins
from docopt import docopt
import readline
import sys
from threading import Lock

from lib.components.network import Network
from lib.components.contract import _ContractBase, _ContractMethod
from lib.services import color, config
CONFIG = config.CONFIG


__doc__ = """Usage: brownie console [options]

Options:
  -h --help             Display this message
  -n --network <name>   Use a specific network (default {})
  --verbose          Enable verbose reporting
  --tb               Show entire python traceback on exceptions

Connects to the network and opens the brownie console.
""".format(CONFIG['network_defaults']['name'])


class Console:

    def __init__(self):
        self._print_lock = Lock()
        self._multiline = False
        self._prompt = ">>> "
        self.__dict__.update({'dir': self._dir})

    def _run(self):
        local_ = {}
        builtins.print = self._print
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
                    r = local_['_result']
                    if r != None:
                        if type(r) is dict and r:
                            color.json(r)
                        else:
                            print(repr(r))
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
        return color('module')
    try:
        if issubclass(type(obj), _ContractBase):
            return color('contract')
        if issubclass(type(obj), _ContractMethod):
            return color('contract_method')
    except TypeError:
        pass
    if not callable(obj):
        return color('value')
    return color('callable')

def main():
    args = docopt(__doc__)

    console = Console()

    network = Network(console)
    print("Brownie environment is ready.")

    console._run()
    network.save()