#!/usr/bin/python3

import sys
import traceback
from pathlib import Path
from typing import Dict, Optional, Sequence

from brownie._config import ARGV, CONFIG

if sys.platform == "win32":
    import colorama

    colorama.init()


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

TB_BASE = (
    "  {0[dull]}File {0[string]}{1[1]}{0[dull]}, line "
    "{0[value]}{1[3]}{0[dull]}, in {0[callable]}{1[5]}{0}{2}"
)

NOTIFY_COLORS = {"WARNING": "error", "ERROR": "error", "SUCCESS": "success"}

base_path = str(Path(".").absolute())


class Color:
    def __call__(self, color=None):
        if color in CONFIG["colors"]:
            color = CONFIG["colors"][color]
        if not color:
            return BASE + "m"
        color = color.split()
        try:
            if len(color) == 2:
                return f"{BASE}{MODIFIERS[color[0]]}{COLORS[color[1]]}m"
            return f"{BASE}{COLORS[color[0]]}m"
        except KeyError:
            return BASE + "m"

    def __str__(self):
        return BASE + "m"

    def __getitem__(self, color):
        return self(color)

    # format dicts for console printing
    def pretty_dict(self, value: Dict, _indent: int = 0) -> str:
        text = ""
        if not _indent:
            text = f"{self['dull']}{{"
        _indent += 4
        for c, k in enumerate(sorted(value.keys(), key=lambda k: str(k))):
            if c:
                text += ","
            s = "'" if isinstance(k, str) else ""
            text += f"\n{' '*_indent}{s}{self['key']}{k}{self['dull']}{s}: "
            if isinstance(value[k], dict):
                text += "{" + self.pretty_dict(value[k], _indent)
                continue
            if isinstance(value[k], (list, tuple, set)):
                text += str(value[k])[0] + self.pretty_sequence(value[k], _indent)
                continue
            text += self._write(value[k])
        _indent -= 4
        text += f"\n{' '*_indent}}}"
        if not _indent:
            text += f"{self}"
        return text

    # format lists for console printing
    def pretty_sequence(self, value: Sequence, _indent: int = 0) -> str:
        text = ""
        brackets = str(value)[0], str(value)[-1]
        if not _indent:
            text += f"{self['dull']}{brackets[0]}"
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
        if not _indent:
            text += f"{self}"
        return text

    def _write(self, value):
        s = '"' if isinstance(value, str) else ""
        key = "string" if isinstance(value, str) else "value"
        return f"{s}{self[key]}{value}{self['dull']}{s}"

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
        if filename and not ARGV["tb"]:
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
            tb[i] = TB_BASE.format(self, info_lines, "\n" + code if code else "")
        tb.append(f"{self['error']}{type(exc).__name__}{self}: {exc}")
        return "\n".join(tb)

    def format_syntaxerror(self, exc: SyntaxError) -> str:
        offset = exc.offset + len(exc.text.lstrip()) - len(exc.text) + 3  # type: ignore
        exc.filename = exc.filename.replace(base_path, ".")
        return (
            f"  {self['dull']}File \"{self['string']}{exc.filename}{self['dull']}\", line "
            f"{self['value']}{exc.lineno}{self['dull']},\n{self}    {exc.text.strip()}\n"
            f"{' '*offset}^\n{self['error']}SyntaxError{self}: {exc.msg}"
        )


def notify(type_, msg):
    """Prepends a message with a colored tag and outputs it to the console."""
    color = Color()
    print(f"{color(NOTIFY_COLORS[type_])}{type_}{color}: {msg}")
