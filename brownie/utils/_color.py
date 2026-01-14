#!/usr/bin/python3

import sys
import traceback
from collections.abc import Sequence
from typing import Any, Final, Literal, cast, final

import pygments
from pygments.formatter import Formatter
from pygments.formatters import get_formatter_by_name
from pygments.lexers import PythonLexer
from pygments_lexer_solidity import SolidityLexer
from vyper.exceptions import VyperException

from brownie._c_constants import Path
from brownie._config import CONFIG

if sys.platform == "win32":
    import colorama

    colorama.init()

fmt_name = "terminal"
try:
    import curses

    curses.setupterm()
    if curses.tigetnum("colors") == 256:
        fmt_name = "terminal256"
except Exception:
    # if curses won't import we are probably using Windows
    pass

COLOR_STYLE: str = CONFIG.settings["console"]["color_style"]
formatter: Final[Formatter] = get_formatter_by_name(fmt_name, style=COLOR_STYLE)

if fmt_name == "terminal256" and COLOR_STYLE == "monokai":
    # dirty hack to make tree diagrams not have a fixed black blackground
    formatter.style_string["Token.Error"] = ("\x1b[0;2;37m", "\x1b[0;m")

BASE: Final = "\x1b[0;"

MODIFIERS: Final = {"bright": "1;", "dark": "2;"}

COLORS: Final = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
}


NotifyType = Literal["SUCCESS", "WARNING", "ERROR"]
NOTIFY_COLORS: Final = {"WARNING": "bright red", "ERROR": "bright red", "SUCCESS": "bright green"}

base_path: Final = str(Path(".").absolute())


# cached color strings

blue: Final = "\x1b[0;34m"  # Color()("blue")
bright_black: Final = "\x1b[0;1;30m"  # Color()("bright black")
bright_blue: Final = "\x1b[0;1;34m"  # Color()("bright blue")
bright_cyan: Final = "\x1b[0;1;36m"  # Color()("bright cyan")
bright_green: Final = "\x1b[0;1;32m"  # Color()("bright green")
bright_magenta: Final = "\x1b[0;1;35m"  # Color()("bright magenta")
bright_red: Final = "\x1b[0;1;31m"  # Color()("bright red")
bright_yellow: Final = "\x1b[0;1;33m"  # Color()("bright yellow")
dark_white: Final = "\x1b[0;2;37m"  # Color()("dark white")
green: Final = "\x1b[0;1;32m"  # Color()("green")
red: Final = "\x1b[0;1;31m"  # Color()("red")
yellow: Final = "\x1b[0;1;33m"  # Color()("yellow")


@final
class Color:
    __cache__: Final[dict[str | None, str]] = {}

    def __call__(self, color_str: str | None = None) -> str:
        if not CONFIG.settings["console"]["show_colors"]:
            return ""
        try:
            return Color.__cache__[color_str]
        except KeyError:
            if not color_str:
                return f"{BASE}m"
            try:
                if " " in color_str:
                    modifier, color_str = color_str.split()
                    color = f"{BASE}{MODIFIERS[modifier]}{COLORS[color_str]}m"
                else:
                    color = f"{BASE}{COLORS[color_str]}m"
            except (KeyError, ValueError):
                color = f"{BASE}m"
            Color.__cache__[color_str] = color
            return color

    def __str__(self):
        return f"{BASE}m"

    # format dicts for console printing
    def pretty_dict(self, value: dict, _indent: int = 0) -> str:
        text = ""
        if not _indent:
            text = "{"
        _indent += 4
        for c, k in enumerate(sorted(value.keys(), key=str)):
            v = value[k]
            if c:
                text += ","
            s = "'" if isinstance(k, str) else ""
            text += f"\n{' '*_indent}{s}{k}{s}: "
            if isinstance(v, dict):
                text += "{" + self.pretty_dict(v, _indent)
                continue
            if isinstance(v, (list, tuple, set)):
                text += str(v)[0] + self.pretty_sequence(v, _indent)  # type: ignore [arg-type]
                continue
            text += self._write(v)
        _indent -= 4
        text += f"\n{' '*_indent}}}"
        return text

    # format lists for console printing
    def pretty_sequence(self, value: Sequence, _indent: int = 0) -> str:
        text = ""
        string = str(value)
        start_bracket, stop_bracket = string[0], string[-1]
        if not _indent:
            text += f"{start_bracket}"
        if value and not [i for i in value if not isinstance(i, dict)]:
            # list of dicts
            text += f"\n{' '*(_indent+4)}{{"
            text += f",\n{' '*(_indent+4)}{{".join(self.pretty_dict(i, _indent + 4) for i in value)
            text += f"\n{' '*_indent}{stop_bracket}"
        elif value and not [i for i in value if not isinstance(i, str) or len(i) != 64]:
            # list of bytes32 hexstrings (stack trace)
            text += ", ".join(f"\n{' '*(_indent+4)}{self._write(i)}" for i in value)
            text += f"\n{' '*_indent}{stop_bracket}"
        else:
            # all other cases
            text += ", ".join(self._write(i) for i in value)
            text += stop_bracket
        return text

    def _write(self, value: Any) -> str:
        s = '"' if isinstance(value, str) else ""
        return f"{s}{value}{s}"

    def format_tb(
        self,
        exc: BaseException,
        filename: str | None = None,
        start: int | None = None,
        stop: int | None = None,
    ) -> str:
        if isinstance(exc, SyntaxError) and exc.text is not None:
            return self.format_syntaxerror(exc)

        tb = [i.replace("./", "") for i in traceback.format_tb(exc.__traceback__)]
        if filename and not CONFIG.argv["tb"]:
            try:
                start = tb.index(next(i for i in tb if filename in i))
                stop = tb.index(next(i for i in tb[::-1] if filename in i)) + 1
            except Exception:
                pass

        tb = tb[start:stop]
        for i in range(len(tb)):
            info, code = tb[i].split("\n")[:2]
            info = info.replace(base_path, ".")
            info_lines = [x.strip(",") for x in info.strip().split(" ")]
            if "site-packages/" in info_lines[1]:
                info_lines[1] = '"' + info_lines[1].split("site-packages/")[1]
            tb[i] = (
                f"  {dark_white}File {bright_magenta}{info_lines[1]}"
                f"{dark_white}, line {bright_blue}{info_lines[3]}"
                f"{dark_white}, in {bright_cyan}{info_lines[5]}{BASE}m"
            )
            if code:
                tb[i] += f"\n{code}"

        msg = str(exc)
        if isinstance(exc, VyperException):
            # apply syntax highlight and remove traceback on vyper exceptions
            msg = self.highlight(msg)
            if not CONFIG.argv["tb"]:
                tb.clear()

        from brownie.exceptions import CompilerError

        if isinstance(exc, CompilerError):
            # apply syntax highlighting on solc exceptions
            if exc.compiler == "solc":
                msg = self.highlight(msg, SolidityLexer())
            else:
                msg = self.highlight(msg)
            if not CONFIG.argv["tb"]:
                tb.clear()

        tb.append(f"{bright_red}{type(exc).__name__}{BASE}m: {msg}")
        return "\n".join(tb)

    def format_syntaxerror(self, exc: SyntaxError) -> str:
        text = cast(str, exc.text)
        offset = cast(int, exc.offset) + len(text.lstrip()) - len(text) + 3
        exc.filename = cast(str, exc.filename).replace(base_path, ".")
        return (
            f'  {dark_white}File "{bright_magenta}{exc.filename}'
            f'{dark_white}", line {bright_blue}{exc.lineno}'
            f"{dark_white},\n{BASE}m    {text.strip()}\n"
            f"{' '*offset}^\n{bright_red}SyntaxError{BASE}m: {exc.msg}"
        )

    def highlight(self, text, lexer=PythonLexer()):
        """
        Apply syntax highlighting to a string.
        """
        return pygments.highlight(text, lexer, formatter)


def notify(type_: NotifyType, msg):
    """Prepends a message with a colored tag and outputs it to the console."""
    color = Color()
    print(f"{color(NOTIFY_COLORS[type_])}{type_}{BASE}m: {msg}")
