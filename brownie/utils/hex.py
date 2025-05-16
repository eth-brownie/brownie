from typing import Final
from importlib.metadata import version

from eth_typing import HexStr
from hexbytes import HexBytes


HEXBYTES_LT_1_0_0: Final = tuple(int(i) for i in version("hexbytes").split(".")) < (
    1,
    0,
    0,
)

if HEXBYTES_LT_1_0_0:
    def hexstring(value: bytes) -> HexStr:
        return HexBytes(value).hex()

else:

    def hexstring(value: bytes) -> HexStr:
        return f"0x{HexBytes(value).hex()}"
