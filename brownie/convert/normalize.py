#!/usr/bin/python3

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from eth_abi.grammar import ABIType, TupleType, parse

from .datatypes import EthAddress, HexString, ReturnValue
from .main import to_bool, to_decimal, to_int, to_string, to_uint
from .utils import get_type_strings


def format_input(abi: Dict, inputs: Union[List, Tuple]) -> List:
    # Format contract inputs based on ABI types
    if len(inputs) and not len(abi["inputs"]):
        raise TypeError(f"{abi['name']} requires no arguments")
    abi_types = _get_abi_types(abi["inputs"])
    try:
        return _format_tuple(abi_types, inputs)
    except Exception as e:
        raise type(e)(f"{abi['name']} {e}") from None


def format_output(abi: Dict, outputs: Union[List, Tuple]) -> ReturnValue:
    # Format contract outputs based on ABI types
    abi_types = _get_abi_types(abi["outputs"])
    result = _format_tuple(abi_types, outputs)
    return ReturnValue(result, abi["outputs"])


def format_event(event: Dict) -> Any:
    # Format event data based on ABI types
    if not event["decoded"]:
        topics = [
            {"type": "bytes32", "name": f"topic{c}", "value": i}
            for c, i in enumerate(event.get("topics", []), start=1)
        ]
        event["data"] = topics + [
            {"type": "bytes", "name": "data", "value": _format_single("bytes", event["data"])}
        ]
        if "anonymous" in event:
            event["name"] = "(anonymous)"
        else:
            event["name"] = "(unknown)"
        return event

    for e in [i for i in event["data"] if not i["decoded"]]:
        e["type"] = "bytes32"
        e["name"] += " (indexed)"
    abi_types = _get_abi_types(event["data"])
    values = ReturnValue(
        _format_tuple(abi_types, [i["value"] for i in event["data"]]), event["data"]
    )
    for i in range(len(event["data"])):
        event["data"][i]["value"] = values[i]
    return event


def _format_tuple(abi_types: Sequence[ABIType], values: Union[List, Tuple]) -> List:
    result = []
    _check_array(values, len(abi_types))
    for type_, value in zip(abi_types, values):
        try:
            if type_.is_array:
                result.append(_format_array(type_, value))
            elif isinstance(type_, TupleType):
                result.append(_format_tuple(type_.components, value))
            else:
                result.append(_format_single(type_.to_type_str(), value))
        except Exception as e:
            raise type(e)(f"'{value}' - {e}") from None
    return result


def _format_array(abi_type: ABIType, values: Union[List, Tuple]) -> List:
    _check_array(values, None if not len(abi_type.arrlist[-1]) else abi_type.arrlist[-1][0])
    item_type = abi_type.item_type
    if item_type.is_array:
        return [_format_array(item_type, i) for i in values]
    elif isinstance(item_type, TupleType):
        return [_format_tuple(item_type.components, i) for i in values]
    return [_format_single(item_type.to_type_str(), i) for i in values]


def _format_single(type_str: str, value: Any) -> Any:
    # Apply standard formatting to a single value
    if "uint" in type_str:
        return to_uint(value, type_str)
    elif "int" in type_str:
        return to_int(value, type_str)
    elif type_str == "fixed168x10":
        return to_decimal(value)
    elif type_str == "bool":
        return to_bool(value)
    elif type_str == "address":
        return EthAddress(value)
    elif "byte" in type_str:
        return HexString(value, type_str)
    elif "string" in type_str:
        return to_string(value)
    raise TypeError(f"Unknown type: {type_str}")


def _check_array(values: Union[List, Tuple], length: Optional[int]) -> None:
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"Expected list or tuple, got {type(values).__name__}")
    if length is not None and len(values) != length:
        raise ValueError(f"Sequence has incorrect length, expected {length} but got {len(values)}")


def _get_abi_types(abi_params: List) -> Sequence[ABIType]:
    if not abi_params:
        return []
    type_str = f"({','.join(get_type_strings(abi_params))})"
    tuple_type = parse(type_str)
    return tuple_type.components
