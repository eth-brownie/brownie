#!/usr/bin/python3

from typing import Any, Dict, Final, List, Optional, Tuple

import eth_hash.auto


keccak: Final = eth_hash.auto.keccak

_cached_int_bounds: Final[Dict[str, Tuple[int, int]]] = {}


def get_int_bounds(type_str: str) -> Tuple[int, int]:
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
    abi_params: List[Dict[str, Any]],
    substitutions: Optional[Dict[str, str]] = None,
) -> List[str]:
    """Converts a list of parameters from an ABI into a list of type strings."""
    types_list = []
    if substitutions is None:
        substitutions = {}

    for i in abi_params:
        if i["type"].startswith("tuple"):
            params = get_type_strings(i["components"], substitutions)
            array_size = i["type"][5:]
            types_list.append(f"({','.join(params)}){array_size}")
        else:
            type_str = i["type"]
            for orig, sub in substitutions.items():
                if type_str.startswith(orig):
                    type_str = type_str.replace(orig, sub)
            types_list.append(type_str)

    return types_list


def build_function_signature(abi: Dict[str, Any]) -> str:
    types_list = get_type_strings(abi["inputs"])
    return f"{abi['name']}({','.join(types_list)})"


def build_function_selector(abi: Dict[str, Any]) -> str:
    sig = build_function_signature(abi)
    return f"0x{keccak(sig.encode()).hex()[:8]}"
