#!/usr/bin/python3

from eth_abi.grammar import TupleType, parse
from hypothesis import strategies as st

from brownie.convert.utils import get_int_bounds
from brownie.network import accounts

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
    return st.sampled_from(list(accounts))


@exclude_filter
def _bytes_strategy(min_size, max_size):
    return st.binary(min_size=min_size, max_size=min_size)


@exclude_filter
def _string_strategy(min_size=0, max_size=1024):
    return st.text(min_size=min_size, max_size=max_size)


def _array_strategy(type_str, min_length=1, max_length=8, unique=False, **kwargs):
    abi_type = parse(type_str)
    if len(abi_type.arrlist[-1]):
        min_len = max_len = abi_type.arrlist[-1][0]
    else:
        if isinstance(min_length, list):
            min_len = min_length.pop()
        else:
            min_len = min_length
        if isinstance(max_length, list):
            max_len = max_length.pop()
        else:
            max_len = max_length
    if abi_type.item_type.is_array:
        kwargs.update(min_length=min_length, max_length=max_length, unique=unique)
    base_strategy = strategy(abi_type.item_type.to_type_str(), **kwargs)
    return st.lists(base_strategy, min_len, max_len, unique=unique)


def _tuple_strategy(type_str):
    abi_type = parse(type_str)
    strategies = [strategy(i.to_type_str()) for i in abi_type.components]
    return st.tuples(*strategies)


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
    if abi_type.is_array:
        return _array_strategy(type_str, **kwargs)
    if isinstance(abi_type, TupleType):
        return _tuple_strategy(type_str, **kwargs)

    base = abi_type.base
    if base in ("int", "uint"):
        return _integer_strategy(type_str, **kwargs)
    if base == "bytes":
        min_size = abi_type.sub or kwargs.pop("min_size", 1)
        max_size = abi_type.sub or kwargs.pop("max_size", 1024)
        return _bytes_strategy(min_size, max_size)

    raise ValueError(f"No strategy available for type: {type_str}")
