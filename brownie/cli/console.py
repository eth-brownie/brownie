#!/usr/bin/python3

import ast
import builtins
from docopt import docopt
import importlib
from pathlib import Path
import sys
import threading

import brownie
import brownie.network as network
from brownie.cli.utils import color
from brownie._config import ARGV, CONFIG

if sys.platform == "win32":
    from pyreadline import Readline
    readline = Readline()
else:
    import readline


__doc__ = """Usage: brownie console [options]

Options:
  --network <name>        Use a specific network (default {})
  --verbose -v            Enable verbose reporting
  --tb -t                 Show entire python traceback on exceptions
  --help -h               Display this message

Connects to the network and opens the brownie console.
""".format(CONFIG['network_defaults']['name'])


class Console:

    def __init__(self):
        self._print_lock = threading.Lock()
        self.__dict__.update({
            'dir': self._dir,
            'run': _run_script
        })
        self.__dict__.update((i, getattr(brownie, i)) for i in brownie.__all__)
        del self.__dict__['project']
        history_file = Path(CONFIG['folders']['project']).joinpath('.history')
        if not history_file.exists():
            history_file.open('w').write("")
        self._readline = str(history_file)
        readline.read_history_file(self._readline)

    def _run(self):
        local_ = {}
        builtins.print = self._print
        while True:
            cmd = self._get_cmd()
            if not cmd:
                continue
            try:
                self._run_cmd(cmd, local_)
            except SystemExit:
                return
            except Exception:
                print(color.format_tb(sys.exc_info(), start=1))

    def _get_cmd(self):
        multiline = False
        self._prompt = ">>> "
        while True:
            try:
                if not multiline:
                    cmd = self._input(self._prompt)
                    if not cmd.strip():
                        return
                    ast.parse(cmd)
                    return cmd
                new_cmd = self._input("... ")
                cmd += "\n" + new_cmd
                ast_type = type(ast.parse(cmd).body[0])
                if ast_type not in (ast.ClassDef, ast.For, ast.FunctionDef) or not new_cmd:
                    return cmd
            except SyntaxError as e:
                if e.msg != "unexpected EOF while parsing":
                    self._prompt = ""
                    print(color.format_tb(sys.exc_info(), start=1))
                    return
                if not multiline:
                    multiline = True
                    self._prompt = "... "
                    continue
                try:
                    ast.parse(cmd+".")
                except IndentationError:
                    return cmd
                except SyntaxError:
                    pass
            except KeyboardInterrupt:
                sys.stdout.write("\nKeyboardInterrupt\n")
                sys.stdout.flush()
                return

    def _run_cmd(self, cmd, local_):
        self._prompt = ""
        local_['__result'] = None
        try:
            exec('__result = ' + cmd, self.__dict__, local_)
        except SyntaxError:
            exec(cmd, self.__dict__, local_)
            return
        result = local_['__result']
        if result is None:
            return
        if result and (type(result) is dict or hasattr(result, '_print_as_dict')):
            color.pretty_dict(result)
        elif type(result) is list or hasattr(result, '_print_as_list'):
            color.pretty_list(result)
        elif type(result) is str:
            print(result)
        else:
            try:
                print(result._console_repr())
            except (AttributeError, TypeError):
                print(repr(result))

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
        if sys.platform == "win32":
            readline.write_history_file(self._readline)
        else:
            readline.append_history_file(1, self._readline)
        return response


def _dir_color(obj):
    if type(obj).__name__ == "module":
        return color('module')
    if hasattr(obj, '_dir_color'):
        return color(obj._dir_color)
    if not callable(obj):
        return color('value')
    return color('callable')


def main():
    args = docopt(__doc__)
    ARGV._update_from_args(args)

    network.connect(ARGV['network'])
    console = Console()
    print("Brownie environment is ready.")

    try:
        console._run()
    except EOFError:
        sys.stdout.write('\n')


def _run_script(module=None, method="main", args=(), kwargs={}):
    '''Loads a module from the scripts/ folder and calls a method.
    If no name is given, returns a list of available scripts.

    Args:
        name (string): name of the script.
        method (string): name of the method to call.
        args (tuple): positional arguments for called method.
        kwargs (dict): keyword arguments for called method.'''
    path = Path(CONFIG['folders']['project']).joinpath('scripts')
    if not module:
        return [i.stem for i in path.glob('[!_]*.py')]
    module = importlib.import_module("scripts."+module)
    return getattr(module, method)(*args, **kwargs)
