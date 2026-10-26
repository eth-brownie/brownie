#!/usr/bin/python3

from collections.abc import Sequence
from typing import Final, TypeGuard, Union

import eth_hash.auto
from eth_typing import ABIComponent, ABIElement, ABIError, ABIEvent, ABIFunction, HexStr

keccak: Final = eth_hash.auto.keccak

_cached_int_bounds: Final[dict[str, tuple[int, int]]] = {}

ABICallable = Union[ABIFunction, ABIEvent, ABIError]


def is_abi_callable(abi_element: ABIElement) -> TypeGuard[ABICallable]:
    return abi_element["type"] in ("function", "error", "event")


def get_int_bounds(type_str: str) -> tuple[int, int]:
    """Returns the lower and upper bound for an integer type."""
    try:
        return _cached_int_bounds[type_str]
    except KeyError:
        # validate input
        size = int(type_str.strip("uint") or 256)
        if size < 8 or size > 256 or size % 8:
            raise ValueError(f"Invalid type: {type_str}")

        # compute lower and upper bound
        if type_str.startswith("u"):
            lower = 0
            upper = 2**size - 1
        else:
            lower = -(2 ** (size - 1))
            upper = 2 ** (size - 1) - 1

        # cache result and return
        _cached_int_bounds[type_str] = lower, upper
        return lower, upper


def get_type_strings(
    abi_params: Sequence[ABIComponent],
    substitutions: dict[str, str] | None = None,
) -> list[str]:
    """Converts a list of parameters from an ABI into a list of type strings."""
    types_list = []
    if substitutions is None:
        substitutions = {}

    for i in abi_params:
        type_str = i["type"]
        if type_str.startswith("tuple"):
            params = get_type_strings(i.get("components", list()), substitutions)
            array_size = type_str[5:]
            types_list.append(f"({','.join(params)}){array_size}")
        else:
            for orig, sub in substitutions.items():
                if type_str.startswith(orig):
                    type_str = type_str.replace(orig, sub)
            types_list.append(type_str)

    return types_list


def build_function_signature(abi: ABICallable) -> str:
    types_list = get_type_strings(abi.get("inputs", list()))
    return f"{abi['name']}({','.join(types_list)})"


def build_function_selector(abi: ABICallable) -> HexStr:
    sig = build_function_signature(abi)
    return f"0x{keccak(sig.encode()).hex()[:8]}"  # type: ignore [return-value]
