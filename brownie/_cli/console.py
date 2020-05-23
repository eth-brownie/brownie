#!/usr/bin/python3

import code
import importlib
import inspect
import re
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from pygments import highlight
from pygments.formatters import get_formatter_by_name
from pygments.lexers import PythonLexer
from pygments.styles import get_style_by_name

import brownie
from brownie import network, project
from brownie._config import CONFIG, _get_data_folder, _update_argv_from_docopt
from brownie.utils import color
from brownie.utils.docopt import docopt

__doc__ = f"""Usage: brownie console [options]

Options:
  --network <name>        Use a specific network (default {CONFIG.settings['networks']['default']})
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

    network.connect(CONFIG.argv["network"])

    shell = Console(active_project)
    shell.interact(banner="Brownie environment is ready.", exitmsg="")


class _Quitter:
    """
    Variation of `_sitebuiltins.Quitter` that does not close `stdin` on exit.

    This class sidesteps an issue with the builtin `exit` and `quit` commands,
    which close `sys.stdin` and so prevent the console from being opened a
    second time. https://bugs.python.org/issue34115#msg322073
    """

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Use {self.name}() or Ctrl-D (i.e. EOF) to exit"

    def __call__(self, code=None):
        raise SystemExit(code)


class Console(code.InteractiveConsole):

    # This value is used as the `input` arg when initializing `prompt_toolkit.PromptSession`.
    # During testing there is a conflict with how pytest supresses stdin/out, so stdin is
    # replaced with `prompt_toolkit.input.defaults.create_pipe_input`
    prompt_input = None

    def __init__(self, project=None, extra_locals=None):
        """
        Launch the Brownie console.

        Arguments
        ---------
        project : `Project`, optional
            Active Brownie project to include in the console's local namespace.
        extra_locals: dict, optional
            Additional variables to add to the console namespace.
        """
        console_settings = CONFIG.settings["console"]

        locals_dict = dict((i, getattr(brownie, i)) for i in brownie.__all__)
        locals_dict.update(_dir=dir, dir=self._dir, exit=_Quitter("exit"), quit=_Quitter("quit"))

        if project:
            project._update_and_register(locals_dict)

        # only make GUI available if Tkinter is installed
        try:
            Gui = importlib.import_module("brownie._gui").Gui
            locals_dict["Gui"] = Gui
        except ModuleNotFoundError:
            pass

        if extra_locals:
            locals_dict.update(extra_locals)

        # prepare lexer and formatter
        self.lexer = PythonLexer()
        fmt_name = "terminal"
        try:
            import curses

            curses.setupterm()
            if curses.tigetnum("colors") == 256:
                fmt_name = "terminal256"
        except Exception:
            # if curses won't import we are probably using Windows
            pass
        self.formatter = get_formatter_by_name(fmt_name, style=console_settings["color_style"])

        # create prompt session object
        history_file = str(_get_data_folder().joinpath(".history").absolute())
        kwargs = {}
        if console_settings["show_colors"]:
            kwargs.update(
                lexer=PygmentsLexer(PythonLexer),
                style=style_from_pygments_cls(get_style_by_name(console_settings["color_style"])),
                include_default_pygments_style=False,
            )
        if console_settings["auto_suggest"]:
            kwargs["auto_suggest"] = TestAutoSuggest(locals_dict)
        if console_settings["completions"]:
            kwargs["completer"] = ConsoleCompleter(locals_dict)

        # add binding for multi-line pastes
        key_bindings = KeyBindings()
        key_bindings.add(Keys.BracketedPaste)(self.paste_event)
        self.compile_mode = "single"

        self.prompt_session = PromptSession(
            history=SanitizedFileHistory(history_file, locals_dict),
            input=self.prompt_input,
            key_bindings=key_bindings,
            **kwargs,
        )

        if console_settings["auto_suggest"]:
            # remove the builtin binding for auto-suggest acceptance
            key_bindings = self.prompt_session.app.key_bindings
            accept_binding = key_bindings.get_bindings_for_keys(("right",))[0]
            key_bindings._bindings2.remove(accept_binding.handler)

        # this is required because of a pytest conflict when using the debugging console
        if sys.platform == "win32":
            import colorama

            colorama.init()

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
        if CONFIG.settings["console"]["show_colors"]:
            text = highlight(text, self.lexer, self.formatter)
        self.write(text)

    def raw_input(self, prompt=""):
        return self.prompt_session.prompt(prompt)

    def paste_event(self, event):
        data = event.data
        data = data.replace("\r\n", "\n")
        data = data.replace("\r", "\n")

        if "\n" in data:
            self.compile_mode = "exec"
        event.current_buffer.insert_text(data)

    def showsyntaxerror(self, filename):
        tb = color.format_tb(sys.exc_info()[1])
        self.write(tb + "\n")

    def showtraceback(self):
        tb = color.format_tb(sys.exc_info()[1], start=1)
        self.write(tb + "\n")

    def runsource(self, source, filename="<input>", symbol="single"):
        mode = self.compile_mode
        self.compile_mode = "single"

        try:
            code = self.compile(source, filename, mode)
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
        return color("brownie blue")
    if hasattr(obj, "_dir_color"):
        return color(obj._dir_color)
    if not callable(obj):
        return color("bright blue")
    return color("bright cyan")


class SanitizedFileHistory(FileHistory):
    """
    FileHistory subclass to strip sensetive information prior to writing to disk.

    Any callable containing a `_private` attribute will have it's input arguments
    removed prior to inclusion in the history file. For example, when the user
    input is:

        Accounts.add("0x1234...")

    The line saved to the history file is:

        Accounts.add()

    The original value is still available within the in-memory history while the
    session is active.
    """

    def __init__(self, filename, local_dict):
        self.locals = local_dict
        super().__init__(filename)

    def store_string(self, line):
        try:
            cls_, method = line[: line.index("(")].split(".")
            method = getattr(self.locals[cls_], method)
            if hasattr(method, "_private"):
                line = line[: line.index("(")] + "()"
        except (ValueError, AttributeError, KeyError):
            pass
        return super().store_string(line)


class ConsoleCompleter(Completer):
    def __init__(self, local_dict):
        self.locals = local_dict
        super().__init__()

    def get_completions(self, document, complete_event):
        try:
            base, current = _parse_document(self.locals, document.text)

            if isinstance(base, dict):
                completions = sorted(base)
            else:
                completions = dir(base)
            if current:
                completions = [i for i in completions if i.startswith(current)]
            else:
                completions = [i for i in completions if not i.startswith("_")]
            for key in completions:
                yield Completion(key, start_position=-len(current))

        except Exception:
            return


class TestAutoSuggest(AutoSuggest):
    """
    AutoSuggest subclass to display contract input hints.

    If an object has an `_autosuggest` method, it is used to build the suggestion.
    Otherwise, names and default values are pulled from `__code__` and `__defaults__`
    respectively.
    """

    def __init__(self, local_dict):
        self.locals = local_dict
        super().__init__()

    def get_suggestion(self, buffer, document):
        try:
            if "(" not in document.text or ")" in document.text:
                return
            method, args = document.text.rsplit("(", maxsplit=1)
            base, current = _parse_document(self.locals, method)

            if isinstance(base, dict):
                obj = base[current]
            else:
                obj = getattr(base, current)
            if inspect.isclass(obj):
                obj = obj.__init__
            elif (
                callable(obj)
                and not hasattr(obj, "_autosuggest")
                and not inspect.ismethod(obj)
                and not inspect.isfunction(obj)
            ):
                # object is a callable class instance
                obj = obj.__call__

            if hasattr(obj, "_autosuggest"):
                inputs = obj._autosuggest()
            else:
                inputs = [f" {i}" for i in obj.__code__.co_varnames[: obj.__code__.co_argcount]]
                if obj.__defaults__:
                    for i in range(-1, -1 - len(obj.__defaults__), -1):
                        inputs[i] = f"{inputs[i]}={obj.__defaults__[i]}"
                if inputs and inputs[0] in (" self", " cls"):
                    inputs = inputs[1:]
            if not args and not inputs:
                return Suggestion(")")

            args = args.split(",")
            inputs[0] = inputs[0][1:]
            remaining_inputs = inputs[len(args) - 1 :]
            remaining_inputs[0] = remaining_inputs[0][len(args[-1]) :]

            return Suggestion(",".join(remaining_inputs) + ")")

        except Exception:
            return


def _parse_document(local_dict, text):
    if "=" in text:
        text = text.split("=")[-1]

    text = text.lstrip()
    attributes = text.split(".")
    current_text = attributes.pop()

    base = local_dict
    for key in attributes:
        if "[" in key:
            key, idx = re.match(r"^(\w+)\[([-0-9]+)\]$", key).groups()
            base = _get_obj(base, key)[int(idx)]
        else:
            base = _get_obj(base, key)

    return base, current_text


def _get_obj(obj, key):
    if isinstance(obj, dict):
        return obj[key]
    return getattr(obj, key)
