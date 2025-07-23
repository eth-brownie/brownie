#!/usr/bin/python3

from typing import Final

from . import hex
from ._color import Color, notify

color: Final = Color()
bytes_to_hexstring: Final = hex.bytes_to_hexstring
hexbytes_to_hexstring: Final = hex.hexbytes_to_hexstring

__all__ = ["Color", "color", "notify", "bytes_to_hexstring", "hexbytes_to_hexstring"]


# cached colors

blue: Final = color("blue")
bright_black: Final = color("bright black")
bright_blue: Final = color("bright blue")
bright_cyan: Final = color("bright cyan")
bright_green: Final = color("bright green")
bright_magenta: Final = color("bright magenta")
bright_red: Final = color("bright red")
bright_yellow: Final = color("bright yellow")
dark_white: Final = color("dark white")
green: Final = color("green")
red: Final = color("red")
yellow: Final = color("yellow")
