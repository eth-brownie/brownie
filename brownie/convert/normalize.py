#!/usr/bin/python3

from typing import Any, Final, List, Optional, Sequence, Tuple, cast

from eth_event.main import DecodedEvent, NonDecodedEvent
from eth_typing import ABIComponent, ABIFunction
from faster_eth_abi.grammar import ABIType, TupleType, parse

from brownie.typing import FormattedEvent

from .datatypes import EthAddress, HexString, ReturnValue
from .main import to_bool, to_decimal, to_int, to_string, to_uint
from .utils import get_type_strings

AnyListOrTuple = List[Any] | Tuple[Any, ...]

# Internal C constants

_TupleType: Final = TupleType

_parse: Final = parse


def format_input(abi: ABIFunction, inputs: AnyListOrTuple) -> List[Any]:
    """Format contract inputs based on ABI types."""
    abi_inputs = abi["inputs"]
    if len(inputs) and not len(abi_inputs):
        raise TypeError(f"{abi['name']} requires no arguments")
    abi_types = _get_abi_types(abi_inputs)
    try:
        return _format_tuple(abi_types, inputs)
    except Exception as e:
        raise type(e)(f"{abi['name']} {e}") from None


def format_output(abi: ABIFunction, outputs: AnyListOrTuple) -> ReturnValue:
    """Format contract outputs based on ABI types."""
    abi_outputs = abi["outputs"]
    abi_types = _get_abi_types(abi_outputs)
    result = _format_tuple(abi_types, outputs)
    return ReturnValue(result, abi_outputs)


def format_event(event: DecodedEvent | NonDecodedEvent) -> FormattedEvent:
    """Format event data based on ABI types."""
    if not event["decoded"]:
        topics = (
            {"type": "bytes32", "name": name, "value": data}
            for name, data in zip(("topic1", "topic2", "topic3"), event.get("topics", ()))
        )
        event["data"] = [  # type: ignore [typeddict-item]
            *topics,
            {"type": "bytes", "name": "data", "value": _format_single("bytes", event["data"])},
        ]
        event["name"] = "(anonymous)" if "anonymous" in event else "(unknown)"  # type: ignore [typeddict-item]
        return event  # type: ignore [return-value]

    data = event["data"]
    for e in data:
        if not e["decoded"]:
            e["type"] = "bytes32"
            e["name"] += " (indexed)"
    abi_types = _get_abi_types(cast(Sequence[ABIComponent], data))
    event_values = [i["value"] for i in data]
    values = ReturnValue(
        _format_tuple(abi_types, event_values),
        cast(Sequence[ABIComponent], data),
    )
    for e, value in zip(data, values):
        e["value"] = value
    return cast(FormattedEvent, event)


def _format_tuple(abi_types: Sequence[ABIType], values: AnyListOrTuple) -> List[Any]:
    result = []
    _check_array(values, len(abi_types))
    for type_, value in zip(abi_types, values):
        try:
            if type_.is_array:
                result.append(_format_array(type_, value))
            elif isinstance(type_, _TupleType):
                result.append(_format_tuple(type_.components, value))
            else:
                result.append(_format_single(type_.to_type_str(), value))
        except Exception as e:
            raise type(e)(f"'{value}' - {e}") from None
    return result


def _format_array(abi_type: ABIType, values: AnyListOrTuple) -> List[Any]:
    arrlist_last = cast(Sequence[str], abi_type.arrlist)[-1]
    _check_array(values, arrlist_last[0] if arrlist_last else None)  # type: ignore [arg-type]
    item_type = abi_type.item_type
    if item_type.is_array:
        return [_format_array(item_type, i) for i in values]
    elif isinstance(item_type, _TupleType):
        item_type_components = item_type.components
        return [_format_tuple(item_type_components, i) for i in values]
    item_type_str = item_type.to_type_str()
    return [_format_single(item_type_str, i) for i in values]


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


def _check_array(values: AnyListOrTuple, length: Optional[int]) -> None:
    if not isinstance(values, (list, tuple)):
        # NOTE: we keep this check here in case the user is running in interpreted mode
        raise TypeError(f"Expected list or tuple, got {type(values).__name__}")
    if length is not None and len(values) != length:
        raise ValueError(f"Sequence has incorrect length, expected {length} but got {len(values)}")


def _get_abi_types(abi_params: Sequence[ABIComponent]) -> Sequence[ABIType]:
    if not abi_params:
        return []
    type_str = f"({','.join(get_type_strings(abi_params))})"
    tuple_type = _parse(type_str)
    return tuple_type.components
