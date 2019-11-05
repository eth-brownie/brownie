#!/usr/bin/python3

from copy import deepcopy
from typing import Any, Dict, ItemsView, KeysView, List, Tuple, TypeVar, Union

import eth_utils
from hexbytes import HexBytes

UNITS = {
    "wei": 0,
    "kwei": 3,
    "babbage": 3,
    "mwei": 6,
    "lovelace": 6,
    "gwei": 9,
    "shannon": 9,
    "microether": 12,
    "szabo": 12,
    "milliether": 15,
    "finney": 15,
    "ether": 18,
}

WeiInputTypes = TypeVar("WeiInputTypes", str, float, int, None)


class Wei(int):

    '''Integer subclass that converts a value to wei and allows comparison against
    similarly formatted values.

    Useful for the following formats:
        * a string specifying the unit: "10 ether", "300 gwei", "0.25 shannon"
        * a large float in scientific notation, where direct conversion to int
          would cause inaccuracy: 8.3e32
        * bytes: b'\xff\xff'
        * hex strings: "0x330124"'''

    # Known typing error: https://github.com/python/mypy/issues/4290
    def __new__(cls, value: Any) -> Any:  # type: ignore
        return super().__new__(cls, _to_wei(value))  # type: ignore

    def __hash__(self) -> int:
        return super().__hash__()

    def __lt__(self, other: Any) -> bool:
        return super().__lt__(_to_wei(other))

    def __le__(self, other: Any) -> bool:
        return super().__le__(_to_wei(other))

    def __eq__(self, other: Any) -> bool:
        try:
            return super().__eq__(_to_wei(other))
        except TypeError:
            return False

    def __ne__(self, other: Any) -> bool:
        try:
            return super().__ne__(_to_wei(other))
        except TypeError:
            return True

    def __ge__(self, other: Any) -> bool:
        return super().__ge__(_to_wei(other))

    def __gt__(self, other: Any) -> bool:
        return super().__gt__(_to_wei(other))

    def __add__(self, other: Any) -> "Wei":
        return Wei(super().__add__(_to_wei(other)))

    def __sub__(self, other: Any) -> "Wei":
        return Wei(super().__sub__(_to_wei(other)))


def _to_wei(value: WeiInputTypes) -> int:
    original = value
    if value is None:
        return 0
    if isinstance(value, bytes):
        value = HexBytes(value).hex()
    if isinstance(value, float) and "e+" in str(value):
        num_str, dec = str(value).split("e+")
        num = num_str.split(".") if "." in num_str else [num_str, ""]
        return int(num[0] + num[1][: int(dec)] + "0" * (int(dec) - len(num[1])))
    if not isinstance(value, str):
        return _return_int(original, value)
    if value[:2] == "0x":
        return int(value, 16)
    for unit, dec in UNITS.items():
        if " " + unit not in value:
            continue
        num_str = value.split(" ")[0]
        num = num_str.split(".") if "." in num_str else [num_str, ""]
        return int(num[0] + num[1][: int(dec)] + "0" * (int(dec) - len(num[1])))
    return _return_int(original, value)


def _return_int(original: Any, value: Any) -> int:
    try:
        return int(value)
    except ValueError:
        raise TypeError(f"Could not convert {type(original)} '{original}' to wei.")


def to_uint(value: Any, type_: str = "uint256") -> "Wei":
    """Convert a value to an unsigned integer"""
    wei: "Wei" = Wei(value)
    size = _check_int_size(type_)
    if wei < 0 or wei >= 2 ** int(size):
        raise OverflowError(f"{value} is outside allowable range for {type_}")
    return wei


def to_int(value: Any, type_: str = "int256") -> "Wei":
    """Convert a value to a signed integer"""
    wei = Wei(value)
    size = _check_int_size(type_)
    if wei < -2 ** int(size) // 2 or wei >= 2 ** int(size) // 2:
        raise OverflowError(f"{value} is outside allowable range for {type_}")
    return wei


def _check_int_size(type_: Any) -> int:
    size = int(type_.strip("uint") or 256)
    if size < 8 or size > 256 or size // 8 != size / 8:
        raise ValueError(f"Invalid type: {type_}")
    return size


class EthAddress(str):

    """String subclass that raises TypeError when compared to a non-address."""

    def __new__(cls, value: Any) -> str:  # type: ignore
        return super().__new__(cls, to_address(value))  # type: ignore

    def __eq__(self, other: Any) -> bool:
        return _address_compare(str(self), other)

    def __ne__(self, other: Any) -> bool:
        return not _address_compare(str(self), other)


def _address_compare(a: Any, b: Any) -> bool:
    b = str(b)
    if not b.startswith("0x") or not eth_utils.is_hex(b) or len(b) != 42:
        raise TypeError(f"Invalid type for comparison: '{b}' is not a valid address")
    return a.lower() == b.lower()


def to_address(value: str) -> str:
    """Convert a value to an address"""
    if isinstance(value, bytes):
        value = HexBytes(value).hex()
    value = eth_utils.add_0x_prefix(str(value))
    try:
        return eth_utils.to_checksum_address(value)
    except ValueError:
        raise ValueError(f"'{value}' is not a valid ETH address.") from None


class HexString(bytes):

    """Bytes subclass for hexstring comparisons. Raises TypeError if compared to
    a non-hexstring. Evaluates True for hexstrings with the same value but differing
    leading zeros or capitalization."""

    def __new__(cls, value, type_):  # type: ignore
        return super().__new__(cls, to_bytes(value, type_))  # type: ignore

    def __eq__(self, other: Any) -> bool:
        return _hex_compare(self.hex(), other)

    def __ne__(self, other: Any) -> bool:
        return not _hex_compare(self.hex(), other)

    def __str__(self) -> str:
        return "0x" + self.hex()

    def __repr__(self) -> str:
        return str(self)


def _hex_compare(a: Any, b: Any) -> bool:
    b = str(b)
    if not b.startswith("0x") or not eth_utils.is_hex(b):
        raise TypeError(f"Invalid type for comparison: '{b}' is not a valid hex string")
    return a.lstrip("0x").lower() == b.lstrip("0x").lower()


def to_bytes(value: Any, type_: str = "bytes32") -> bytes:
    """Convert a value to bytes"""
    if not isinstance(value, (bytes, str, int)):
        raise TypeError(f"'{value}', type {type(value)}, cannot convert to {type_}")
    value = bytes_to_hex(value)
    if type_ == "bytes":
        return eth_utils.to_bytes(hexstr=value)
    if type_ == "byte":
        type_ = "bytes1"
    size = int(type_.strip("bytes"))
    if size < 1 or size > 32:
        raise ValueError(f"Invalid type: {type_}")
    try:
        return int(value, 16).to_bytes(size, "big")
    except OverflowError:
        raise OverflowError(f"'{value}' exceeds maximum length for {type_}")


def bytes_to_hex(value: Any) -> str:
    """Convert a bytes value to a hexstring"""
    if isinstance(value, bytes):
        return HexBytes(value).hex()
    if isinstance(value, int):
        return hex(value)
    if isinstance(value, str) and eth_utils.is_hex(value):
        return eth_utils.add_0x_prefix(value)
    raise ValueError(f"Cannot convert {type(value)} '{value}' to a hex string.")


def to_bool(value: Any) -> bool:
    """Convert a value to a boolean"""
    if not isinstance(value, (int, float, bool, bytes, str)):
        raise TypeError(f"Cannot convert {type(value)} '{value}' to bool")
    if isinstance(value, bytes):
        value = HexBytes(value).hex()
    if isinstance(value, str) and value.startswith("0x"):
        value = int(value, 16)
    if value not in (0, 1, True, False):
        raise ValueError(f"Cannot convert {type(value)} '{value}' to bool")
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


def _format_input(abi: Dict, inputs: Union[List, Tuple]) -> "ReturnValue":
    # Format contract inputs based on ABI types
    if len(inputs) and not len(abi["inputs"]):
        raise TypeError(f"{abi['name']} requires no arguments")
    try:
        return _format_abi(abi["inputs"], inputs)
    except Exception as e:
        raise type(e)(f"{abi['name']} {e}") from None


def _format_output(abi: Dict, outputs: Tuple) -> "ReturnValue":
    # Format contract outputs based on ABI types
    return _format_abi(abi["outputs"], outputs)


def _format_event(event: Dict) -> Any:
    # Format event data based on ABI types
    for e in [i for i in event["data"] if not i["decoded"]]:
        e["type"] = "bytes32"
        e["name"] += " (indexed)"
    values = _format_abi(event["data"], [i["value"] for i in event["data"]])
    for i in range(len(event["data"])):
        event["data"][i]["value"] = values[i]
    return event


def _format_abi(abi: Any, values: Any) -> "ReturnValue":
    # Apply standard formatting to multiple values of differing types
    types = [i["type"] for i in abi]
    values = list(values)
    if len(values) != len(types):
        raise TypeError(f"Expected {len(types)} arguments, got {len(values)}: {','.join(types)}")
    for i, type_ in enumerate(types):
        try:
            if "]" in type_:
                values[i] = _format_array(abi[i], values[i])
            elif type_ == "tuple":
                values[i] = _format_abi(abi[i]["components"], values[i])
            else:
                values[i] = _format_single(type_, values[i])
        except Exception as e:
            raise type(e)(f"argument #{i}: '{values[i]}' - {e}")
    return ReturnValue(values, abi)


def _format_array(abi: Any, values: Any) -> "ReturnValue":
    # Apply standard formatting to multiple values of the same type (arrays)
    base_type, length = abi["type"][:-1].rsplit("[", maxsplit=1)
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"Expected sequence, got {type(values)}")
    if length != "" and len(values) != int(length):
        raise ValueError(f"Expected {abi['type']} but sequence has length of {len(values)}")
    if "]" in base_type:
        abi = deepcopy(abi)
        abi["type"] = base_type
        return ReturnValue([_format_array(abi, i) for i in values])
    if base_type == "tuple":
        abi = abi["components"]
        return ReturnValue([_format_abi(abi, i) for i in values], abi)
    return ReturnValue([_format_single(base_type, i) for i in values])


def _format_single(type_: str, value: Any) -> Any:
    # Apply standard formatting to a single value
    if "uint" in type_:
        return to_uint(value, type_)
    elif "int" in type_:
        return to_int(value, type_)
    elif type_ == "bool":
        return to_bool(value)
    elif type_ == "address":
        return EthAddress(value)
    elif "byte" in type_:
        return HexString(value, type_)
    elif "string" in type_:
        return to_string(value)
    raise TypeError(f"Unknown type: {type_}")


class ReturnValue(tuple):
    """Tuple subclass with dict-like functionality, used for iterable return values."""

    def __new__(cls, values: Any, abi: Any = None) -> "ReturnValue":
        self = super().__new__(cls, values)  # type: ignore
        self._abi = abi or []  # type: ignore
        self._dict = {}  # type: ignore
        for c, i in enumerate(self._abi):  # type: ignore
            if not i["name"]:
                continue
            self._dict[i["name"]] = values[c]  # type: ignore
        return self

    def __hash__(self) -> Any:
        return super().__hash__()

    def __eq__(self, other: Any) -> Any:
        return _kwargtuple_compare(self, other)

    def __getitem__(self, key: Any) -> Any:
        if type(key) is slice:
            abi = deepcopy(self._abi)[key]  # type: ignore
            result = super().__getitem__(key)
            return ReturnValue(result, abi)
        if isinstance(key, int):
            return super().__getitem__(key)
        return self._dict[key]  # type: ignore

    def __contains__(self, value: Any) -> bool:
        return self.count(value) > 0

    def count(self, value: Any) -> int:
        """ReturnValue.count(value) -> integer -- return number of occurrences of value"""
        count = 0
        for item in self:
            try:
                if _kwargtuple_compare(item, value):
                    count += 1
            except TypeError:
                continue
        return count

    def dict(self) -> Dict:
        """ReturnValue.dict() -> a dictionary of ReturnValue's named items"""
        return self._dict  # type: ignore

    def index(self, value: Any, start: int = 0, stop: Any = None) -> int:
        """ReturnValue.index(value, [start, [stop]]) -> integer -- return first index of value.
        Raises ValueError if the value is not present."""
        if stop is None:
            stop = len(self)
        for i in range(start, stop):
            try:
                if _kwargtuple_compare(self[i], value):
                    return i
            except TypeError:
                continue
        raise ValueError(f"{value} is not in ReturnValue")

    def items(self) -> ItemsView:
        """ReturnValue.items() -> a set-like object providing a view on ReturnValue's named items"""
        return self._dict.items()  # type: ignore

    def keys(self) -> KeysView:
        """ReturnValue.keys() -> a set-like object providing a view on ReturnValue's keys"""
        return self._dict.keys()  # type: ignore


def _kwargtuple_compare(a: Any, b: Any) -> Any:
    if not isinstance(a, (tuple, list, ReturnValue)):
        types_ = set([type(a), type(b)])
        if types_.intersection([bool, type(None)]):
            return a is b
        if types_.intersection([dict, EthAddress, HexString]):
            return a == b
        return _convert_str(a) == _convert_str(b)
    if not isinstance(b, (tuple, list, ReturnValue)) or len(b) != len(a):
        return False
    return next((False for i in range(len(a)) if not _kwargtuple_compare(a[i], b[i])), True)


def _convert_str(value: Any) -> "Wei":
    if not isinstance(value, str):
        if not hasattr(value, "address"):
            return value
        value = value.address
    if value.startswith("0x"):
        return "0x" + value.lstrip("0x").lower()
    if value.count(" ") != 1:
        return value
    try:
        return Wei(value)
    except ValueError:
        return value
