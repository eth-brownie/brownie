#!/usr/bin/python3

import builtins
from docopt import docopt
from pathlib import Path
import readline
import sys
from threading import Lock

import brownie
import brownie.network as network
from brownie.network.contract import _ContractBase, _ContractMethod
from brownie.types import StrictDict, KwargTuple
from brownie.cli.utils import color
import brownie.config as config
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
        self.__dict__.update((i, getattr(brownie, i)) for i in brownie.__all__)
        del self.__dict__['project']
        history_file = Path(CONFIG['folders']['project']).joinpath('.history')
        if not history_file.exists():
            history_file.open('w').write("")
        self._readline = str(history_file)

    def _run(self):
        local_ = {}
        builtins.print = self._print
        readline.read_history_file(self._readline)
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
                            try:
                                print(r._console_repr())
                            except TypeError:
                                print(repr(r))
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
        readline.append_history_file(1, self._readline)
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

    network.connect(config.ARGV['network'], True)
    console = Console()
    print("Brownie environment is ready.")

    try:
        console._run()
    except EOFError:
        sys.stdout.write('\n')
