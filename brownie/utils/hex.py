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

if HEXBYTES_LT_1_0_0:

    def hexstring(value: bytes) -> HexStr:
        """Convert a bytes value to a hexstring on hexbytes<1."""
        return HexBytes(value).hex()

else:

    def hexstring(value: bytes) -> HexStr:
        """Convert a bytes value to a hexstring on hexbytes>=1."""
        return f"0x{HexBytes(value).hex()}"
