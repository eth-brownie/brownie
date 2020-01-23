#!/usr/bin/python3

from eth_abi.grammar import parse
from eth_utils import to_checksum_address
from hypothesis import strategies as st

from brownie.convert.utils import get_int_bounds

TYPE_STR_TRANSLATIONS = {"byte": "bytes1", "decimal": "fixed168x10"}


def exclude_filter(fn):
    def wrapper(*args, exclude=None, **kwargs):
        strat = fn(*args, **kwargs)
        if exclude is None:
            return strat
        return strat.filter(lambda k: k not in exclude)

    return wrapper


@exclude_filter
def _integer_strategy(type_str, min_value=None, max_value=None):
    lower, upper = get_int_bounds(type_str)
    if min_value is None:
        min_value = lower
    if max_value is None:
        max_value = upper
    return st.integers(min_value, max_value)


@exclude_filter
def _decimal_strategy(min_value=None, max_value=None, places=10):
    lower, upper = get_int_bounds("int128")
    if min_value is None:
        min_value = lower
    if max_value is None:
        max_value = upper
    return st.decimals(min_value, max_value, places=places)


@exclude_filter
def _address_strategy():
    return st.binary(min_size=20, max_size=20).map(to_checksum_address)


@exclude_filter
def _bytes_strategy(min_size, max_size):
    return st.binary(min_size=min_size, max_size=min_size)


@exclude_filter
def _string_strategy(min_size=0, max_size=1024):
    return st.text(min_size=min_size, max_size=max_size)


def strategy(type_str, **kwargs):
    type_str = TYPE_STR_TRANSLATIONS.get(type_str, type_str)
    if type_str == "fixed168x10":
        return _decimal_strategy(**kwargs)
    if type_str == "address":
        return _address_strategy(**kwargs)
    if type_str == "bool":
        return st.booleans(**kwargs)
    if type_str == "string":
        return _string_strategy(**kwargs)

    abi_type = parse(type_str)
    base = abi_type.base
    if base in ("int", "uint"):
        return _integer_strategy(type_str, **kwargs)
    if base == "bytes":
        min_size = abi_type.sub or kwargs.pop("min_size", 1)
        max_size = abi_type.sub or kwargs.pop("max_size", 1024)
        return _bytes_strategy(min_size, max_size)

    raise ValueError(f"No strategy available for type: {type_str}")
