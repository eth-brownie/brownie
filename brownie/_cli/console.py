#!/usr/bin/python3

import builtins
import code
import importlib
import inspect
import sys
import tokenize
from collections.abc import Iterable
from io import StringIO

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles.pygments import style_from_pygments_cls
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
  --no-compile            Use previous contracts compilation

Connects to the network and opens the brownie console.
"""

_parser_cache: dict = {}


def main():
    args = docopt(__doc__)
    _update_argv_from_docopt(args)

    if project.check_for_project():
        active_project = project.load()
        active_project.load_config()
        active_project._add_to_main_namespace()
        print(f"{active_project._name} is the active project.")
    else:
        active_project = None
        sys.path.insert(0, "")
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


class ConsolePrinter:
    """
    Custom printer during console input.

    Ensures that stdout of the active prompt buffer is preserved when the console
    is written to during user imnut.
    """

    _builtins_print = builtins.print

    def __init__(self, console):
        self.console = console

    def start(self):
        builtins.print = self

    def __call__(self, *values, sep=" ", end="\n", file=sys.stdout, flush=False):
        if file != sys.stdout:
            self._builtins_print(*values, sep=sep, end=end, file=file, flush=flush)
            return

        ps = sys.ps2 if self.console.buffer else sys.ps1
        line = f"{ps}{self.console.prompt_session.app.current_buffer.text}"

        # overwrite the prompt output with whitespace, in case the printed data is shorter
        self.console.write(f"\r{' ' * len(line)}\r")

        if not end.endswith("\n"):
            end = "{end}\n"
        text = f"{sep.join(str(i) for i in values)}{end}{line}"
        self.console.write(text)

    def finish(self):
        builtins.print = self._builtins_print


class Console(code.InteractiveConsole):

    # This value is used as the `input` arg when initializing `prompt_toolkit.PromptSession`.
    # During testing there is a conflict with how pytest supresses stdin/out, so stdin is
    # replaced with `prompt_toolkit.input.defaults.create_pipe_input`
    prompt_input = None

    def __init__(self, project=None, extra_locals=None, exit_on_continue=False):
        """
        Launch the Brownie console.

        Arguments
        ---------
        project : `Project`, optional
            Active Brownie project to include in the console's local namespace.
        extra_locals: dict, optional
            Additional variables to add to the console namespace.
        exit_on_continue: bool, optional
            If True, the `continue` command causes the console to
            raise a SystemExit with error message "continue".
        """
        console_settings = CONFIG.settings["console"]

        locals_dict = dict((i, getattr(brownie, i)) for i in brownie.__all__)
        locals_dict.update(
            _dir=dir, dir=self._dir, exit=_Quitter("exit"), quit=_Quitter("quit"), _console=self
        )

        self.exit_on_continue = exit_on_continue
        if exit_on_continue:
            # add continue to the locals so we can quickly reach it via completion hints
            locals_dict["continue"] = True

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
            kwargs["auto_suggest"] = ConsoleAutoSuggest(self, locals_dict)
        if console_settings["completions"]:
            kwargs["completer"] = ConsoleCompleter(self, locals_dict)
        if console_settings["editing_mode"]:
            kwargs["editing_mode"] = EditingMode(console_settings["editing_mode"].upper())

        self.compile_mode = "single"
        self.prompt_session = PromptSession(
            history=SanitizedFileHistory(history_file, locals_dict),
            input=self.prompt_input,
            key_bindings=KeyBindings(),
            **kwargs,
        )

        # add custom bindings
        key_bindings = self.prompt_session.key_bindings
        key_bindings.add(Keys.BracketedPaste)(self.paste_event)

        key_bindings.add("c-i")(self.tab_event)
        key_bindings.get_bindings_for_keys(("c-i",))[-1].filter = lambda: not self.tab_filter()

        # modify default bindings
        key_bindings = load_key_bindings()
        key_bindings.get_bindings_for_keys(("c-i",))[-1].filter = self.tab_filter

        if console_settings["auto_suggest"]:
            # remove the builtin binding for auto-suggest acceptance
            key_bindings = self.prompt_session.app.key_bindings
            accept_binding = key_bindings.get_bindings_for_keys(("right",))[0]
            key_bindings._bindings2.remove(accept_binding.handler)

        # this is required because of a pytest conflict when using the debugging console
        if sys.platform == "win32":
            import colorama

            colorama.init()

        self.console_printer = ConsolePrinter(self)
        super().__init__(locals_dict)

    def _dir(self, obj=None):
        # console dir method, for simplified and colorful output
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
            text = color.highlight(text)
        self.write(text)

    def interact(self, *args, **kwargs):
        # temporarily modify mode so that container repr's display correctly for console
        cli_mode = CONFIG.argv["cli"]
        CONFIG.argv["cli"] = "console"
        try:
            super().interact(*args, **kwargs)
        finally:
            CONFIG.argv["cli"] = cli_mode

    def raw_input(self, prompt=""):
        self.console_printer.start()
        try:
            return self.prompt_session.prompt(prompt)
        finally:
            self.console_printer.finish()

    def showsyntaxerror(self, filename):
        tb = color.format_tb(sys.exc_info()[1])
        self.write(tb + "\n")

    def showtraceback(self):
        tb = color.format_tb(sys.exc_info()[1], start=1)
        self.write(tb + "\n")

    def resetbuffer(self):
        # reset the input buffer and parser cache
        _parser_cache.clear()
        return super().resetbuffer()

    def runsource(self, source, filename="<input>", symbol="single"):
        mode = self.compile_mode
        self.compile_mode = "single"

        if source == "continue" and self.exit_on_continue:
            # used to differentiate exit and continue for pytest interactive debugging
            raise SystemExit("continue")

        try:
            code = self.compile(source, filename, mode)
        except (OverflowError, SyntaxError, ValueError):
            self.showsyntaxerror(filename)
            return False

        if code is None:
            # multiline statement
            return True

        try:
            self.compile(source, filename, "eval")
            code = self.compile(f"__ret_value__ = {source}", filename, "exec")
        except Exception:
            pass
        self.runcode(code)
        if "__ret_value__" in self.locals and self.locals["__ret_value__"] is not None:
            return_value = self.locals.pop("__ret_value__")
            self._console_write(return_value)
        return False

    def paste_event(self, event):
        # pasting multiline data temporarily switches to multiline mode
        data = event.data
        data = data.replace("\r\n", "\n")
        data = data.replace("\r", "\n")

        if "\n" in data:
            self.compile_mode = "exec"
        event.current_buffer.insert_text(data)

    def tab_event(self, event):
        # for multiline input, pressing tab at the start of a new line adds four spaces
        event.current_buffer.insert_text("    ")

    def tab_filter(self):
        # detect multiline input with no meaningful text on the current line
        return not self.buffer or self.prompt_session.app.current_buffer.text.strip()


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
    def __init__(self, console, local_dict):
        self.console = console
        self.locals = local_dict
        super().__init__()

    def get_completions(self, document, complete_event):
        try:
            text = "\n".join(self.console.buffer + [document.text])
            base, current = _parse_document(self.locals, text)[:2]

            if isinstance(base[-1], dict):
                completions = sorted(base[-1], key=lambda k: str(k))
            else:
                completions = dir(base[-1])

            if current:
                completions = [i for i in completions if i.startswith(current)]
            else:
                completions = [i for i in completions if not i.startswith("_")]
            for key in completions:
                yield Completion(key, start_position=-len(current))

        except Exception:
            return


class ConsoleAutoSuggest(AutoSuggest):
    """
    AutoSuggest subclass to display contract input hints.

    If an object has an `_autosuggest` method, it is used to build the suggestion.
    Otherwise, names and default values are pulled from `__code__` and `__defaults__`
    respectively.
    """

    def __init__(self, console, local_dict):
        self.console = console
        self.locals = local_dict
        super().__init__()

    def get_suggestion(self, buffer, document):
        try:
            text = "\n".join(self.console.buffer + [document.text])
            base, _, comma_data = _parse_document(self.locals, text)

            # find the active function call
            del base[-1]
            while base[-1] == self.locals:
                del base[-1]
                del comma_data[-1]
            obj = base[-1]

            # calculate distance from last comma
            count, offset = comma_data[-1]
            lines = text.count("\n") + 1
            if offset[0] < lines:
                distance = len(document.text)
            else:
                distance = len(document.text) - offset[1]

            if hasattr(obj, "_autosuggest"):
                inputs = obj._autosuggest(obj)
            else:
                inputs = [f" {i}" for i in obj.__code__.co_varnames[: obj.__code__.co_argcount]]
                if obj.__defaults__:
                    for i in range(-1, -1 - len(obj.__defaults__), -1):
                        inputs[i] = f"{inputs[i]}={obj.__defaults__[i]}"
                if inputs and inputs[0] in (" self", " cls"):
                    inputs = inputs[1:]
            if not count and not inputs:
                return Suggestion(")")

            inputs[0] = inputs[0][1:]
            remaining_inputs = inputs[count:]
            remaining_inputs[0] = remaining_inputs[0][distance:]

            return Suggestion(f"{','.join(remaining_inputs)})")

        except Exception:
            return


def _obj_from_token(obj, token):
    key = token.string
    if isinstance(obj, dict):
        return obj[key]
    if isinstance(obj, Iterable):
        try:
            return obj[int(key)]
        except ValueError:
            pass
    return getattr(obj, key)


def _parse_document(local_dict, text):
    if text in _parser_cache:
        if _parser_cache[text] is None:
            raise SyntaxError

        # return copies of lists so we can mutate them without worry
        active_objects, current_text, comma_data = _parser_cache[text]
        return active_objects.copy(), current_text, comma_data.copy()

    last_token = None
    active_objects = [local_dict]
    pending_active = []

    # number of open parentheses
    paren_count = 0

    # is a square bracket open?
    is_open_sqb = False

    # number of comments at this call depth, end offset of the last comment
    comma_data = [(0, (0, 0))]

    token_iter = tokenize.generate_tokens(StringIO(text).readline)
    while True:
        try:
            token = next(token_iter)
        except (tokenize.TokenError, StopIteration):
            break

        if token.exact_type in (0, 4):
            # end marker, newline
            break

        if token.exact_type in (5, 6, 61):
            # indent, dedent, non-terminating newline
            # these can be ignored
            continue

        if token.type == 54 and token.string not in ",.[]()":
            # if token is an operator or delimiter but not a parenthesis or dot, this is
            # the start of a new expression. restart evaluation from the next token.
            last_token = None
            active_objects[-1] = local_dict
            continue

        if token.exact_type == 8:
            # right parenthesis `)`
            paren_count -= 1
            del comma_data[-1]
            del active_objects[-1]
            last_token = None
            if active_objects[-1] != local_dict:
                try:
                    pending_active = active_objects[-1].__annotations__["return"]
                    if isinstance(pending_active, str):
                        module = sys.modules[active_objects[-1].__module__]
                        pending_active = getattr(module, pending_active)
                except (AttributeError, KeyError):
                    pending_active = None
                active_objects[-1] = None

        elif token.exact_type == 10:
            # right square bracket `]`
            if not is_open_sqb:
                # no support for nested index references or multiple keys
                _parser_cache[text] = None
                raise SyntaxError
            is_open_sqb = False
            del comma_data[-1]
            del active_objects[-1]

            pending_active = None
            if active_objects[-1] != local_dict:
                try:
                    # try to get the actual object first
                    pending_active = _obj_from_token(active_objects[-1], last_token)
                except (AttributeError, TypeError):
                    # if we can't get the object, use the return type from the annotation
                    try:
                        func = active_objects[-1].__getitem__.__func__
                        pending_active = func.__annotations__["return"]
                        if isinstance(pending_active, str):
                            module = sys.modules[active_objects[-1].__module__]
                            pending_active = getattr(module, pending_active)
                    except (AttributeError, KeyError):
                        pass
                except Exception:
                    pass
                active_objects[-1] = None
            last_token = None

        elif token.exact_type == 12:
            # comma `,`
            comma_data[-1] = (comma_data[-1][0] + 1, token.end)
            last_token = None
            active_objects[-1] = local_dict
            pending_active = None

        elif token.exact_type == 23:
            # period `.`
            if pending_active:
                active_objects[-1] = pending_active
                pending_active = None
            else:
                active_objects[-1] = _obj_from_token(active_objects[-1], last_token)
            last_token = None

        elif token.exact_type == 7:
            # left parenthesis `(`
            if pending_active:
                active_objects[-1] = pending_active
                pending_active = None

            if last_token:
                obj = _obj_from_token(active_objects[-1], last_token)

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

                # ensure we aren't looking at a decorator
                if hasattr(obj, "__wrapped__"):
                    obj = obj.__wrapped__

                active_objects[-1] = obj
                last_token = None
                if not hasattr(active_objects[-1], "__call__"):
                    raise SyntaxError

            paren_count += 1
            comma_data.append((0, token.end))
            active_objects.append(local_dict)

        elif token.exact_type == 9:
            # left square bracket `[`
            if is_open_sqb:
                _parser_cache[text] = None
                raise SyntaxError

            if pending_active:
                active_objects[-1] = pending_active
                pending_active = None

            if last_token:
                active_objects[-1] = _obj_from_token(active_objects[-1], last_token)
                last_token = None
                if not hasattr(active_objects[-1], "__getitem__"):
                    raise SyntaxError

            is_open_sqb = True
            comma_data.append((0, token.end))
            active_objects.append(local_dict)

        else:
            if pending_active or last_token:
                _parser_cache[text] = None
                raise SyntaxError
            last_token = token

    # if the final token is a name or number, it is the current text we are basing
    # the completion suggestion on. otherwise, there is no current text.
    current_text = ""
    if text.endswith(" "):
        active_objects[-1] = local_dict
    elif last_token and last_token.type in (1, 2, 3):
        current_text = last_token.string

    _parser_cache[text] = (active_objects, current_text, comma_data)
    return active_objects.copy(), current_text, comma_data.copy()
