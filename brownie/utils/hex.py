from typing import Final
from importlib.metadata import version

from eth_typing import HexStr
from hexbytes import HexBytes


HEXBYTES_LT_1_0_0: Final = tuple(int(i) for i in version("hexbytes").split(".")) < (
    1,
    0,
    0,
)
"""
A boolean constant that indicates if the version of your `hexbytes` package is less than 1.0.0.

This exists to address a breaking change in hexbytes v1 and allow brownie to be used with either version.
"""


def bytes_to_hexstring(value: bytes) -> HexStr:
    """Convert a bytes value to a hexstring on hexbytes<1."""
    return f"0x{value.hex()}"


def hexbytes_to_hexstring(value: HexBytes) -> HexStr:
    """Convert a HexBytes object to a hex string."""


if HEXBYTES_LT_1_0_0:

    hexbytes_to_hexstring = HexBytes.hex

else:

    hexbytes_to_hexstring = bytes_to_hexstring
