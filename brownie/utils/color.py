#!/usr/bin/python3

import sys
import traceback
from pathlib import Path
from typing import Dict, Optional, Sequence

import pygments
from pygments.formatters import get_formatter_by_name
from pygments.lexers import PythonLexer
from pygments_lexer_solidity import SolidityLexer
from vyper.exceptions import VyperException

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

formatter = get_formatter_by_name(fmt_name, style=CONFIG.settings["console"]["color_style"])


BASE = "\x1b[0;"

MODIFIERS = {"bright": "1;", "dark": "2;"}

COLORS = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
}

NOTIFY_COLORS = {"WARNING": "bright red", "ERROR": "bright red", "SUCCESS": "bright green"}

base_path = str(Path(".").absolute())


class Color:
    def __call__(self, color_str: str = None) -> str:
        if not CONFIG.settings["console"]["show_colors"]:
            return ""
        if not color_str:
            return BASE + "m"
        try:
            if " " not in color_str:
                return f"{BASE}{COLORS[color_str]}m"
            modifier, color_str = color_str.split()
            return f"{BASE}{MODIFIERS[modifier]}{COLORS[color_str]}m"
        except (KeyError, ValueError):
            return BASE + "m"

    def __str__(self):
        return BASE + "m"

    # format dicts for console printing
    def pretty_dict(self, value: Dict, _indent: int = 0) -> str:
        text = ""
        if not _indent:
            text = "{"
        _indent += 4
        for c, k in enumerate(sorted(value.keys(), key=lambda k: str(k))):
            if c:
                text += ","
            s = "'" if isinstance(k, str) else ""
            text += f"\n{' '*_indent}{s}{k}{s}: "
            if isinstance(value[k], dict):
                text += "{" + self.pretty_dict(value[k], _indent)
                continue
            if isinstance(value[k], (list, tuple, set)):
                text += str(value[k])[0] + self.pretty_sequence(value[k], _indent)
                continue
            text += self._write(value[k])
        _indent -= 4
        text += f"\n{' '*_indent}}}"
        return text

    # format lists for console printing
    def pretty_sequence(self, value: Sequence, _indent: int = 0) -> str:
        text = ""
        brackets = str(value)[0], str(value)[-1]
        if not _indent:
            text += f"{brackets[0]}"
        if value and not [i for i in value if not isinstance(i, dict)]:
            # list of dicts
            text += f"\n{' '*(_indent+4)}{{"
            text += f",\n{' '*(_indent+4)}{{".join(self.pretty_dict(i, _indent + 4) for i in value)
            text += f"\n{' '*_indent}{brackets[1]}"
        elif value and not [i for i in value if not isinstance(i, str) or len(i) != 64]:
            # list of bytes32 hexstrings (stack trace)
            text += ", ".join(f"\n{' '*(_indent+4)}{self._write(i)}" for i in value)
            text += f"\n{' '*_indent}{brackets[1]}"
        else:
            # all other cases
            text += ", ".join(self._write(i) for i in value)
            text += brackets[1]
        return text

    def _write(self, value):
        s = '"' if isinstance(value, str) else ""
        return f"{s}{value}{s}"

    def format_tb(
        self,
        exc: Exception,
        filename: str = None,
        start: Optional[int] = None,
        stop: Optional[int] = None,
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
                f"  {self('dark white')}File {self('bright magenta')}{info_lines[1]}"
                f"{self('dark white')}, line {self('bright blue')}{info_lines[3]}"
                f"{self('dark white')}, in {self('bright cyan')}{info_lines[5]}{self}"
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

        tb.append(f"{self('bright red')}{type(exc).__name__}{self}: {msg}")
        return "\n".join(tb)

    def format_syntaxerror(self, exc: SyntaxError) -> str:
        offset = exc.offset + len(exc.text.lstrip()) - len(exc.text) + 3  # type: ignore
        exc.filename = exc.filename.replace(base_path, ".")
        return (
            f"  {self('dark white')}File \"{self('bright magenta')}{exc.filename}"
            f"{self('dark white')}\", line {self('bright blue')}{exc.lineno}"
            f"{self('dark white')},\n{self}    {exc.text.strip()}\n"
            f"{' '*offset}^\n{self('bright red')}SyntaxError{self}: {exc.msg}"
        )

    def highlight(self, text, lexer=PythonLexer()):
        """
        Apply syntax highlighting to a string.
        """
        return pygments.highlight(text, lexer, formatter)


def notify(type_, msg):
    """Prepends a message with a colored tag and outputs it to the console."""
    color = Color()
    print(f"{color(NOTIFY_COLORS[type_])}{type_}{color}: {msg}")
