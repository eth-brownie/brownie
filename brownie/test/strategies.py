#!/usr/bin/python3

from typing import Any, Callable, Iterable, Optional, Tuple, Union

from eth_abi.grammar import BasicType, TupleType, parse
from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy
from hypothesis.strategies._internal.deferred import DeferredStrategy

from brownie import network, project
from brownie.convert import Fixed, Wei
from brownie.convert.utils import get_int_bounds

TYPE_STR_TRANSLATIONS = {"byte": "bytes1", "decimal": "fixed168x10"}

ArrayLengthType = Union[int, list, None]
NumberType = Union[float, int, None]


class _DeferredStrategyRepr(DeferredStrategy):
    def __init__(self, fn: Callable, repr_target: str) -> None:
        super().__init__(fn)
        self._repr_target = repr_target

    def __repr__(self):
        return f"sampled_from({self._repr_target})"


def _exclude_filter(fn: Callable) -> Callable:
    def wrapper(*args: Tuple, exclude: Any = None, **kwargs: int) -> SearchStrategy:
        strat = fn(*args, **kwargs)
        if exclude is None:
            return strat
        if callable(exclude):
            return strat.filter(exclude)
        if not isinstance(exclude, Iterable) or isinstance(exclude, str):
            exclude = (exclude,)
        strat = strat.filter(lambda k: k not in exclude)
        # make the filter repr more readable
        repr_ = strat.__repr__().rsplit(").filter", maxsplit=1)[0]
        strat._cached_repr = f"{repr_}, exclude={exclude})"
        return strat

    return wrapper


def _check_numeric_bounds(
    type_str: str, min_value: NumberType, max_value: NumberType, num_class: type
) -> Tuple:
    lower, upper = get_int_bounds(type_str)
    min_final = lower if min_value is None else num_class(min_value)
    max_final = upper if max_value is None else num_class(max_value)
    if min_final < lower:
        raise ValueError(f"min_value '{min_value}' is outside allowable range for {type_str}")
    if max_final > upper:
        raise ValueError(f"max_value '{max_value}' is outside allowable range for {type_str}")
    if min_final > max_final:
        raise ValueError(f"min_value '{min_final}' is greater than max_value '{max_final}'")
    return min_final, max_final


@_exclude_filter
def _integer_strategy(
    type_str: str, min_value: Optional[int] = None, max_value: Optional[int] = None
) -> SearchStrategy:
    min_value, max_value = _check_numeric_bounds(type_str, min_value, max_value, Wei)
    return st.integers(min_value=min_value, max_value=max_value)


@_exclude_filter
def _decimal_strategy(
    min_value: NumberType = None, max_value: NumberType = None, places: int = 10
) -> SearchStrategy:
    min_value, max_value = _check_numeric_bounds("int128", min_value, max_value, Fixed)
    return st.decimals(min_value=min_value, max_value=max_value, places=places)


@_exclude_filter
def _address_strategy(length: Optional[int] = None) -> SearchStrategy:
    return _DeferredStrategyRepr(
        lambda: st.sampled_from(list(network.accounts)[:length]), "accounts"
    )


@_exclude_filter
def _bytes_strategy(
    abi_type: BasicType, min_size: Optional[int] = None, max_size: Optional[int] = None
) -> SearchStrategy:
    size = abi_type.sub
    if not size:
        return st.binary(min_size=min_size or 1, max_size=max_size or 64)
    if size < 1 or size > 32:
        raise ValueError(f"Invalid type: {abi_type.to_type_str()}")
    if min_size is not None or max_size is not None:
        raise TypeError("Cannot specify size for fixed length bytes strategy")
    return st.binary(min_size=size, max_size=size)


@_exclude_filter
def _string_strategy(min_size: int = 0, max_size: int = 64) -> SearchStrategy:
    return st.text(min_size=min_size, max_size=max_size)


def _get_array_length(var_str: str, length: ArrayLengthType, dynamic_len: int) -> int:
    if not isinstance(length, (list, int)):
        raise TypeError(f"{var_str} must be of type int or list, not '{type(length).__name__}''")
    if not isinstance(length, list):
        return length
    if len(length) != dynamic_len:
        raise ValueError(
            f"Length of '{var_str}' must equal the number of dynamic "
            f"dimensions for the given array ({dynamic_len})"
        )
    return length.pop()


def _array_strategy(
    abi_type: BasicType,
    min_length: ArrayLengthType = 1,
    max_length: ArrayLengthType = 8,
    unique: bool = False,
    **kwargs: Any,
) -> SearchStrategy:
    if abi_type.arrlist[-1]:
        min_len = max_len = abi_type.arrlist[-1][0]
    else:
        dynamic_len = len([i for i in abi_type.arrlist if not i])
        min_len = _get_array_length("min_length", min_length, dynamic_len)
        max_len = _get_array_length("max_length", max_length, dynamic_len)
    if abi_type.item_type.is_array:
        kwargs.update(min_length=min_length, max_length=max_length, unique=unique)
    base_strategy = strategy(abi_type.item_type.to_type_str(), **kwargs)
    strat = st.lists(base_strategy, min_size=min_len, max_size=max_len, unique=unique)
    # swap 'size' for 'length' in the repr
    repr_ = "length".join(strat.__repr__().rsplit("size", maxsplit=2))
    strat._LazyStrategy__representation = repr_  # type: ignore
    return strat


def _tuple_strategy(abi_type: TupleType) -> SearchStrategy:
    strategies = [strategy(i.to_type_str()) for i in abi_type.components]
    return st.tuples(*strategies)


def contract_strategy(contract_name: str) -> SearchStrategy:
    def _contract_deferred(name):
        for proj in project.get_loaded_projects():
            if name in proj.dict():
                return st.sampled_from(list(proj[name]))

        raise NameError(f"Contract '{name}' does not exist in any active projects")

    return _DeferredStrategyRepr(lambda: _contract_deferred(contract_name), contract_name)


def strategy(type_str: str, **kwargs: Any) -> SearchStrategy:
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
        return _array_strategy(abi_type, **kwargs)
    if isinstance(abi_type, TupleType):
        return _tuple_strategy(abi_type, **kwargs)  # type: ignore

    base = abi_type.base
    if base in ("int", "uint"):
        return _integer_strategy(type_str, **kwargs)
    if base == "bytes":
        return _bytes_strategy(abi_type, **kwargs)

    raise ValueError(f"No strategy available for type: {type_str}")
