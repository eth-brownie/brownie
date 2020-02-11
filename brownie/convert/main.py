#!/usr/bin/python3

from decimal import Decimal
from typing import Any

import eth_utils
from hexbytes import HexBytes

from .datatypes import EthAddress, Fixed, HexString, Wei
from .utils import get_int_bounds


def to_uint(value: Any, type_str: str = "uint256") -> Wei:
    """Convert a value to an unsigned integer"""
    wei: Wei = Wei(value)
    lower, upper = get_int_bounds(type_str)
    if wei < lower or wei > upper:
        raise OverflowError(f"{value} is outside allowable range for {type_str}")
    return wei


def to_int(value: Any, type_str: str = "int256") -> Wei:
    """Convert a value to a signed integer"""
    wei = Wei(value)
    lower, upper = get_int_bounds(type_str)
    if wei < lower or wei > upper:
        raise OverflowError(f"{value} is outside allowable range for {type_str}")
    return wei


def to_decimal(value: Any) -> Fixed:
    """Convert a value to a fixed point decimal"""
    d: Fixed = Fixed(value)
    if d < -(2 ** 127) or d >= 2 ** 127:
        raise OverflowError(f"{value} is outside allowable range for decimal")
    if d.quantize(Decimal("1.0000000000")) != d:
        raise ValueError("Maximum of 10 decimal points allowed")
    return d


def to_address(value: str) -> str:
    """Convert a value to an address"""
    return str(EthAddress(value))


def to_bytes(value: Any, type_str: str = "bytes32") -> bytes:
    """Convert a value to bytes"""
    return bytes(HexString(value, type_str))


def to_bool(value: Any) -> bool:
    """Convert a value to a boolean"""
    if not isinstance(value, (int, float, bool, bytes, str)):
        raise TypeError(f"Cannot convert {type(value).__name__} '{value}' to bool")
    if isinstance(value, bytes):
        value = HexBytes(value).hex()
    if isinstance(value, str) and value.startswith("0x"):
        value = int(value, 16)
    if value not in (0, 1, True, False):
        raise ValueError(f"Cannot convert {type(value).__name__} '{value}' to bool")
    return bool(value)


def to_string(value: Any) -> str:
    """Convert a value to a string"""
    if isinstance(value, bytes):
        value = HexBytes(value).hex()
    value = str(value)
    if value.startswith("0x") and eth_utils.is_hex(value):
        try:
            return eth_utils.to_text(hexstr=value)
        except UnicodeDecodeError as e:
            raise ValueError(e)
    return value
