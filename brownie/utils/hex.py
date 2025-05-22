"""This file contains utility funtions for converting bytes values to hexstrings.

Since this code is frequently accessed, instead of adding runtime checks within
the function bodies, we opted to microoptimize by defining functions specific to
your hexbytes version .
"""

from importlib.metadata import version
from typing import Final

from eth_typing import HexStr
from hexbytes import HexBytes

HEXBYTES_LT_1_0_0: Final = tuple(int(i) for i in version("hexbytes").split(".")) < (
    1,
    0,
    0,
)
"""
A boolean constant that indicates if the version of your `hexbytes` package is less than 1.0.0.

This exists to address a breaking change in hexbytes v1 and allow brownie to be used with
either version.
"""


def hexbytes_to_hexstring(value: HexBytes) -> HexStr:
    """Convert a HexBytes object to a hex string."""
    # NOTE: this is just a stub for mypy, the func is conditionally
    # defined below based on your hexbytes version


if HEXBYTES_LT_1_0_0:

    def bytes_to_hexstring(value: bytes) -> HexStr:
        """Convert a bytes value to a hexstring on hexbytes<1."""
        return HexBytes(value).hex()

    hexbytes_to_hexstring = HexBytes.hex
    """Convert a HexBytes value to a hexstring on hexbytes<1."""

else:

    def bytes_to_hexstring(value: bytes) -> HexStr:
        """Convert a bytes value to a hexstring on hexbytes>=1."""
        return f"0x{value.hex()}"

    hexbytes_to_hexstring = bytes_to_hexstring
    """Convert a HexBytes value to a hexstring on hexbytes>=1."""
