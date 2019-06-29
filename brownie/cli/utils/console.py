#!/usr/bin/python3

import builtins
import code
import sys

from . import color

if sys.platform == "win32":
    from pyreadline import Readline
    readline = Readline()
else:
    import readline  # noqa: F401


class Console(code.InteractiveConsole):

    def __init__(self, locals_dict):
        builtins.dir = self._dir
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

    def showtraceback(self):
        tb = color.format_tb(sys.exc_info(), start=1)
        self.write(tb+'\n')


def _dir_color(obj):
    if type(obj).__name__ == "module":
        return color('module')
    if hasattr(obj, '_dir_color'):
        return color(obj._dir_color)
    if not callable(obj):
        return color('value')
    return color('callable')
