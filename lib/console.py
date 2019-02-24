#!/usr/bin/python3

import builtins
from docopt import docopt
import readline
import sys
from threading import Lock

from lib.components.network import Network
from lib.components.contract import _ContractBase, _ContractMethod
from lib.services.datatypes import StrictDict, KwargTuple
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
            open("build/.history", 'w').write("")
        while True:
            if not self._multiline:
                try:
                    cmd = self._input(self._prompt)
                except KeyboardInterrupt:
                    sys.stdout.write("\nUse exit() or Ctrl-D (i.e. EOF) to exit.\n")
                    sys.stdout.flush()
                    continue
                if not cmd.strip():
                    continue
                if cmd.rstrip()[-1] == ":":
                    self._multiline = True
                    self._prompt = "... "
                    continue
            else:
                try:
                    new_cmd = self._input("... ")
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
                    if r is not None:
                        if type(r) in (dict, StrictDict) and r:
                            color.pretty_dict(r)
                        elif type(r) in (list, tuple, KwargTuple):
                            color.pretty_list(r)
                        elif type(r) is str:
                            print(r)
                        elif hasattr(r, '_console_repr'):
                            print(r._console_repr())
                        else:
                            print(repr(r))
                except SyntaxError:
                    exec(cmd, self.__dict__, local_)
                except SystemExit:
                    return
            except:
                print(color.format_tb(sys.exc_info(), start=1))
            self._prompt = ">>> "

    # replaces builtin print method, for threadsafe printing
    def _print(self, *args, sep=' ', end='\n', file=sys.stdout, flush=False):
        with self._print_lock:
            ln = readline.get_line_buffer()
            file.write('\r'+' '*(len(ln)+4)+'\r')
            file.write(sep.join(str(i) for i in args)+end)
            file.write(self._prompt+ln)
            file.flush()

    # replaces builtin dir method, for pretty and easier to read output
    def _dir(self, obj=None):
        if obj is None:
            obj = self
        results = [(i, getattr(obj, i)) for i in builtins.dir(obj) if i[0] != "_"]
        print("["+"{}, ".format(color()).join(
            _dir_color(i[1])+i[0] for i in results
        )+color()+"]")

    # save user input to readline history file, filter for private keys
    def _input(self, prompt):
        response = input(prompt)
        try:
            cls_, method = response[:response.index("(")].split(".")
            cls_ = getattr(self, cls_)
            method = getattr(cls_, method)
            if hasattr(method, "_private"):
                readline.replace_history_item(
                    readline.get_current_history_length() - 1,
                    response[:response.index("(")] + "()"
                )
        except (ValueError, AttributeError):
            pass
        readline.append_history_file(1, "build/.history")
        return response


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
    docopt(__doc__)

    console = Console()
    network = Network(console)
    print("Brownie environment is ready.")

    try:
        console._run()
    except EOFError:
        sys.stdout.write('\n')
    finally:
        network.save()
