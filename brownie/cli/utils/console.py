#!/usr/bin/python3

import builtins
import code
from pathlib import Path
import sys

from . import color

if sys.platform == "win32":
    from pyreadline import Readline
    readline = Readline()
else:
    import readline  # noqa: F401


class Console(code.InteractiveConsole):

    def __init__(self, locals_dict, history_file):
        builtins.dir = self._dir
        self._stdout_write = sys.stdout.write
        sys.stdout.write = self._console_write
        history_file = Path(history_file)
        if not history_file.exists():
            history_file.open('w').write("")
        self._readline = str(history_file)
        readline.read_history_file(self._readline)
        super().__init__(locals_dict)

    # replaces builtin dir method, for simplified and colorful output
    def _dir(self, obj=None):
        if obj is None:
            results = [(k, v) for k, v in self.locals.items() if not k.startswith('_')]
        elif hasattr(obj, '__console_dir__'):
            results = [(i, getattr(obj, i)) for i in obj.__console_dir__]
        else:
            results = [(i, getattr(obj, i)) for i in obj.__dict__ if not i.startswith('_')]
        results = sorted(results, key=lambda k: k[0])
        self.write("["+f"{color}, ".join(_dir_color(i[1])+i[0] for i in results)+f"{color}]\n")

    def _console_write(self, text):
        try:
            obj = eval(text)
            if type(obj) is dict:
                text = color.pretty_dict(obj)
            elif type(obj) in (tuple, list):
                text = color.pretty_list(obj)
        except SyntaxError:
            pass
        return self._stdout_write(text)

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
        except (ValueError, AttributeError):
            pass
        if sys.platform == "win32":
            readline.write_history_file(self._readline)
        else:
            readline.append_history_file(1, self._readline)
        return super().push(line)


def _dir_color(obj):
    if type(obj).__name__ == "module":
        return color('module')
    if hasattr(obj, '_dir_color'):
        return color(obj._dir_color)
    if not callable(obj):
        return color('value')
    return color('callable')
