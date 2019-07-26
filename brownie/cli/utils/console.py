#!/usr/bin/python3

import atexit
import code
from pathlib import Path
import sys

import brownie
from . import color
from brownie._config import CONFIG

if sys.platform == "win32":
    from pyreadline import Readline
    readline = Readline()
else:
    import readline  # noqa: F401


class Console(code.InteractiveConsole):

    def __init__(self):
        locals_dict = dict((i, getattr(brownie, i)) for i in brownie.__all__)
        locals_dict['dir'] = self._dir
        del locals_dict['project']

        self._stdout_write = sys.stdout.write
        sys.stdout.write = self._console_write

        history_file = str(Path(CONFIG['folders']['project']).joinpath('.history').absolute())
        atexit.register(_atexit_readline, history_file)
        try:
            readline.read_history_file(history_file)
        except (FileNotFoundError, OSError):
            pass
        super().__init__(locals_dict)

    # console dir method, for simplified and colorful output
    def _dir(self, obj=None):
        if obj is None:
            results = [(k, v) for k, v in self.locals.items() if not k.startswith('_')]
        elif hasattr(obj, '__console_dir__'):
            results = [(i, getattr(obj, i)) for i in obj.__console_dir__]
        else:
            results = [(i, getattr(obj, i)) for i in dir(obj) if not i.startswith('_')]
        results = sorted(results, key=lambda k: k[0])
        self.write("["+f"{color}, ".join(_dir_color(i[1])+i[0] for i in results)+f"{color}]\n")

    def _console_write(self, text):
        try:
            obj = eval(text)
            if obj and type(obj) is dict:
                text = color.pretty_dict(obj)
            elif obj and type(obj) in (tuple, list, set):
                text = color.pretty_list(obj)
        except (SyntaxError, NameError):
            pass
        return self._stdout_write(text)

    def showsyntaxerror(self, filename):
        tb = color.format_syntaxerror(sys.exc_info()[1])
        self.write(tb+'\n')

    def showtraceback(self):
        tb = color.format_tb(sys.exc_info(), start=1)
        self.write(tb+'\n')

    # save user input to readline history file, filter for private keys
    def push(self, line):
        try:
            cls_, method = line[:line.index("(")].split(".")
            method = getattr(self.locals[cls_], method)
            if hasattr(method, "_private"):
                readline.replace_history_item(
                    readline.get_current_history_length() - 1,
                    line[:line.index("(")] + "()"
                )
        except (ValueError, AttributeError, KeyError):
            pass
        return super().push(line)


def _dir_color(obj):
    if type(obj).__name__ == "module":
        return color('module')
    if hasattr(obj, '_dir_color'):
        return color(obj._dir_color)
    if not callable(obj):
        return color('value')
    return color('callable')


def _atexit_readline(history_file):
    readline.set_history_length(1000)
    readline.write_history_file(history_file)
