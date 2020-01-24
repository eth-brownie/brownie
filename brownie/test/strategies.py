#!/usr/bin/python3

from typing import Callable, Iterable, Optional, Sequence, Tuple

from eth_abi.grammar import BasicType, TupleType, parse
from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from brownie import network
from brownie.convert.utils import get_int_bounds

TYPE_STR_TRANSLATIONS = {"byte": "bytes1", "decimal": "fixed168x10"}


def exclude_filter(fn: Callable) -> Callable:
    def wrapper(*args: Tuple, exclude: Optional[Sequence] = None, **kwargs: int) -> SearchStrategy:
        strat = fn(*args, **kwargs)
        if exclude is None:
            return strat
        if not isinstance(exclude, Iterable) or isinstance(exclude, str):
            exclude = (exclude,)
        return strat.filter(lambda k: k not in exclude)

    return wrapper


@exclude_filter
def _integer_strategy(
    type_str: str, min_value: Optional[int] = None, max_value: Optional[int] = None
) -> SearchStrategy:
    lower, upper = get_int_bounds(type_str)
    return st.integers(min_value=min_value or lower, max_value=max_value or upper)


@exclude_filter
def _decimal_strategy(
    min_value: Optional[int] = None, max_value: Optional[int] = None, places: int = 10
) -> SearchStrategy:
    lower, upper = get_int_bounds("int128")
    if min_value is None:
        min_value = lower
    if max_value is None:
        max_value = upper
    return st.decimals(min_value=min_value, max_value=max_value, places=places)


@exclude_filter
def _address_strategy() -> SearchStrategy:
    return st.sampled_from(list(network.accounts))


@exclude_filter
def _bytes_strategy(
    abi_type: BasicType, min_size: Optional[int] = None, max_size: Optional[int] = None
) -> SearchStrategy:
    size = abi_type.sub
    if not size:
        return st.binary(min_size=min_size or 1, max_size=max_size or 1024)
    if size < 1 or size > 32:
        raise ValueError(f"Invalid type: {abi_type.to_type_str()}")
    if min_size is not None or max_size is not None:
        raise TypeError("Cannot specify size for fixed length bytes strategy")
    return st.binary(min_size=size, max_size=size)


@exclude_filter
def _string_strategy(min_size: int = 0, max_size: int = 1024) -> SearchStrategy:
    return st.text(min_size=min_size, max_size=max_size)


def _array_strategy(
    type_str: str, min_length: int = 1, max_length: int = 8, unique: bool = False, **kwargs: int
) -> SearchStrategy:
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


def _tuple_strategy(type_str: str) -> SearchStrategy:
    abi_type = parse(type_str)
    strategies = [strategy(i.to_type_str()) for i in abi_type.components]
    return st.tuples(*strategies)


def strategy(type_str: str, **kwargs: int) -> SearchStrategy:
    type_str = TYPE_STR_TRANSLATIONS.get(type_str, type_str)
    if type_str == "fixed168x10":
        return _decimal_strategy(**kwargs)
    if type_str == "address":
        return _address_strategy(**kwargs)
    if type_str == "bool":
        return st.booleans(**kwargs)  # type: ignore
    if type_str == "string":
        return _string_strategy(**kwargs)

    abi_type = parse(type_str)
    if abi_type.is_array:
        return _array_strategy(type_str, **kwargs)  # type: ignore
    if isinstance(abi_type, TupleType):
        return _tuple_strategy(type_str, **kwargs)  # type: ignore

    base = abi_type.base
    if base in ("int", "uint"):
        return _integer_strategy(type_str, **kwargs)
    if base == "bytes":
        return _bytes_strategy(abi_type, **kwargs)

    raise ValueError(f"No strategy available for type: {type_str}")
