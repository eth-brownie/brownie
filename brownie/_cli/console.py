#!/usr/bin/python3

import atexit
import code
import importlib
import sys

import brownie
from brownie import network, project
from brownie._config import ARGV, BROWNIE_FOLDER, CONFIG, _update_argv_from_docopt
from brownie.utils import color
from brownie.utils.docopt import docopt

if sys.platform == "win32":
    from pyreadline import Readline

    readline = Readline()
else:
    import readline  # noqa: F401

__doc__ = f"""Usage: brownie console [options]

Options:
  --network <name>        Use a specific network (default {CONFIG['network']['default']})
  --tb -t                 Show entire python traceback on exceptions
  --help -h               Display this message

Connects to the network and opens the brownie console.
"""


def main():
    args = docopt(__doc__)
    _update_argv_from_docopt(args)

    if project.check_for_project():
        active_project = project.load()
        active_project.load_config()
        print(f"{active_project._name} is the active project.")
    else:
        active_project = None
        print("No project was loaded.")

    network.connect(ARGV["network"])

    shell = Console(active_project)
    shell.interact(banner="Brownie environment is ready.", exitmsg="")


class Console(code.InteractiveConsole):
    def __init__(self, project=None):
        locals_dict = dict((i, getattr(brownie, i)) for i in brownie.__all__)
        locals_dict["dir"] = self._dir

        # only make GUI available if Tkinter is installed
        try:
            Gui = importlib.import_module("brownie._gui").Gui
            locals_dict["Gui"] = Gui
        except ModuleNotFoundError:
            pass

        if project:
            project._update_and_register(locals_dict)
            history_file = project._path
        else:
            history_file = BROWNIE_FOLDER

        history_file = str(history_file.joinpath(".history").absolute())
        atexit.register(_atexit_readline, history_file)
        try:
            readline.read_history_file(history_file)
        except (FileNotFoundError, OSError):
            pass
        super().__init__(locals_dict)

    # console dir method, for simplified and colorful output
    def _dir(self, obj=None):
        if obj is None:
            results = [(k, v) for k, v in self.locals.items() if not k.startswith("_")]
        elif hasattr(obj, "__console_dir__"):
            results = [(i, getattr(obj, i)) for i in obj.__console_dir__]
        else:
            results = [(i, getattr(obj, i)) for i in dir(obj) if not i.startswith("_")]
        results = sorted(results, key=lambda k: k[0])
        self.write(f"[{f'{color}, '.join(_dir_color(i[1]) + i[0] for i in results)}{color}]\n")

    def _console_write(self, obj):
        text = repr(obj)
        try:
            if obj and isinstance(obj, dict):
                text = color.pretty_dict(obj)
            elif obj and isinstance(obj, (tuple, list, set)):
                text = color.pretty_sequence(obj)
        except (SyntaxError, NameError):
            pass
        print(text)

    def showsyntaxerror(self, filename):
        tb = color.format_tb(sys.exc_info()[1])
        self.write(tb + "\n")

    def showtraceback(self):
        tb = color.format_tb(sys.exc_info()[1], start=1)
        self.write(tb + "\n")

    # save user input to readline history file, filter for private keys
    def push(self, line):
        try:
            cls_, method = line[: line.index("(")].split(".")
            method = getattr(self.locals[cls_], method)
            if hasattr(method, "_private"):
                readline.replace_history_item(
                    readline.get_current_history_length() - 1, line[: line.index("(")] + "()"
                )
        except (ValueError, AttributeError, KeyError):
            pass
        return super().push(line)

    def runsource(self, source, filename="<input>", symbol="single"):
        try:
            code = self.compile(source, filename, "single")
        except (OverflowError, SyntaxError, ValueError):
            self.showsyntaxerror(filename)
            return False

        if code is None:
            return True

        try:
            self.compile(source, filename, "eval")
            code = self.compile(f"__ret_value__ = {source}", filename, "exec")
        except Exception:
            pass
        self.runcode(code)
        if "__ret_value__" in self.locals and self.locals["__ret_value__"] is not None:
            self._console_write(self.locals["__ret_value__"])
            del self.locals["__ret_value__"]
        return False


def _dir_color(obj):
    if type(obj).__name__ == "module":
        return color("module")
    if hasattr(obj, "_dir_color"):
        return color(obj._dir_color)
    if not callable(obj):
        return color("value")
    return color("callable")


def _atexit_readline(history_file):
    readline.set_history_length(1000)
    readline.write_history_file(history_file)
