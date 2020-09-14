#!/usr/bin/python3

from copy import deepcopy
from decimal import Decimal, getcontext
from typing import Any, Dict, ItemsView, KeysView, List, Optional, Sequence, TypeVar, Union

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

    """Integer subclass that converts a value to wei and allows comparison against
    similarly formatted values.

    Useful for the following formats:
        * a string specifying the unit: "10 ether", "300 gwei", "0.25 shannon"
        * a large float in scientific notation, where direct conversion to int
          would cause inaccuracy: 8.3e32
        * bytes: b'\xff\xff'
        * hex strings: "0x330124\""""

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

    def to(self, unit: str) -> "Fixed":
        """
        Returns a converted denomination of the stored wei value.
        Accepts any valid ether unit denomination as string, like:
        "gwei", "milliether", "finney", "ether".

        :param unit: An ether denomination like "ether" or "gwei"
        :return: A 'Fixed' type number in the specified denomination
        """
        try:
            return Fixed(self * Fixed(10) ** -UNITS[unit])
        except KeyError:
            raise TypeError(f'Cannot convert wei to unknown unit: "{unit}". ') from None


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
        raise TypeError(f"Cannot convert {type(original).__name__} '{original}' to wei.")


class Fixed(Decimal):

    """
    Decimal subclass that allows comparison against strings, integers and Wei.

    Raises TypeError when operations are attempted against floats.
    """

    # Known typing error: https://github.com/python/mypy/issues/4290
    def __new__(cls, value: Any) -> Any:  # type: ignore
        return super().__new__(cls, _to_fixed(value))  # type: ignore

    def __repr__(self) -> str:
        return f"Fixed('{str(self)}')"

    def __hash__(self) -> int:
        return super().__hash__()

    def __lt__(self, other: Any) -> bool:  # type: ignore
        return super().__lt__(_to_fixed(other))

    def __le__(self, other: Any) -> bool:  # type: ignore
        return super().__le__(_to_fixed(other))

    def __eq__(self, other: Any) -> bool:  # type: ignore
        if isinstance(other, float):
            raise TypeError("Cannot compare to floating point - use a string instead")
        try:
            return super().__eq__(_to_fixed(other))
        except TypeError:
            return False

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, float):
            raise TypeError("Cannot compare to floating point - use a string instead")
        try:
            return super().__ne__(_to_fixed(other))
        except TypeError:
            return True

    def __ge__(self, other: Any) -> bool:  # type: ignore
        return super().__ge__(_to_fixed(other))

    def __gt__(self, other: Any) -> bool:  # type: ignore
        return super().__gt__(_to_fixed(other))

    def __add__(self, other: Any) -> "Fixed":  # type: ignore
        return Fixed(super().__add__(_to_fixed(other)))

    def __sub__(self, other: Any) -> "Fixed":  # type: ignore
        return Fixed(super().__sub__(_to_fixed(other)))


def _to_fixed(value: Any) -> Decimal:
    if isinstance(value, float):
        raise TypeError("Cannot convert float to decimal - use a string instead")

    if isinstance(value, (str, bytes)):
        try:
            value = Wei(value)
        except TypeError:
            pass
    try:
        ctx = getcontext()
        ctx.prec = 100
        return Decimal(value, context=ctx)
    except Exception:
        raise TypeError(f"Cannot convert {type(value).__name__} '{value}' to decimal.")


class EthAddress(str):

    """String subclass that raises TypeError when compared to a non-address."""

    def __new__(cls, value: Union[bytes, str]) -> str:
        converted_value = value
        if isinstance(value, bytes):
            converted_value = HexBytes(value).hex()
        converted_value = eth_utils.add_0x_prefix(str(converted_value))  # type: ignore
        try:
            converted_value = eth_utils.to_checksum_address(converted_value)
        except ValueError:
            raise ValueError(f"'{value}' is not a valid ETH address") from None
        return super().__new__(cls, converted_value)  # type: ignore

    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, other: Any) -> bool:
        return _address_compare(str(self), other)

    def __ne__(self, other: Any) -> bool:
        return not _address_compare(str(self), other)


def _address_compare(a: Any, b: Any) -> bool:
    b = str(b)
    if not b.startswith("0x") or not eth_utils.is_hex(b) or len(b) != 42:
        raise TypeError(f"Invalid type for comparison: '{b}' is not a valid address")
    return a.lower() == b.lower()


class HexString(bytes):

    """Bytes subclass for hexstring comparisons. Raises TypeError if compared to
    a non-hexstring. Evaluates True for hexstrings with the same value but differing
    leading zeros or capitalization."""

    def __new__(cls, value, type_str):  # type: ignore
        return super().__new__(cls, _to_bytes(value, type_str))  # type: ignore

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


def _to_bytes(value: Any, type_str: str = "bytes32") -> bytes:
    """Convert a value to bytes"""
    if isinstance(value, bool) or not isinstance(value, (bytes, str, int)):
        raise TypeError(f"Cannot convert {type(value).__name__} '{value}' to {type_str}")
    value = _to_hex(value)
    if type_str == "bytes":
        return eth_utils.to_bytes(hexstr=value)
    if type_str == "byte":
        type_str = "bytes1"
    size = int(type_str.strip("bytes"))
    if size < 1 or size > 32:
        raise ValueError(f"Invalid type: {type_str}")
    try:
        return int(value, 16).to_bytes(size, "big")
    except OverflowError:
        raise OverflowError(f"'{value}' exceeds maximum length for {type_str}")


def _to_hex(value: Any) -> str:
    """Convert a value to a hexstring"""
    if isinstance(value, bytes):
        return HexBytes(value).hex()
    if isinstance(value, int):
        return hex(value)
    if isinstance(value, str):
        if value in ("", "0x"):
            return "0x00"
        if eth_utils.is_hex(value):
            return eth_utils.add_0x_prefix(value)  # type: ignore
    raise ValueError(f"Cannot convert {type(value).__name__} '{value}' to a hex string")


class ReturnValue(tuple):
    """Tuple subclass with dict-like functionality, used for iterable return values."""

    _abi: Optional[List] = None
    _dict: Dict = {}

    def __new__(cls, values: Sequence, abi: Optional[List] = None) -> "ReturnValue":
        values = list(values)
        for i in range(len(values)):
            if isinstance(values[i], (tuple, list)) and not isinstance(values[i], ReturnValue):
                if abi is not None and "components" in abi[i]:
                    if abi[i]["type"] == "tuple":
                        # tuple
                        values[i] = ReturnValue(values[i], abi[i]["components"])
                    else:
                        # array of tuples
                        values[i] = ReturnValue(values[i], [abi[i]] * len(values[i]))
                else:
                    # array
                    values[i] = ReturnValue(values[i])

        self = super().__new__(cls, values)  # type: ignore
        self._abi = abi or []
        self._dict = {i["name"]: values[c] for c, i in enumerate(self._abi) if i["name"]}
        return self

    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, other: Any) -> bool:
        return _kwargtuple_compare(self, other)

    def __getitem__(self, key: Any) -> Any:
        if type(key) is slice:
            abi = None
            if self._abi is not None:
                abi = deepcopy(self._abi)[key]  # type: ignore
            result = super().__getitem__(key)
            return ReturnValue(result, abi)
        if isinstance(key, int):
            return super().__getitem__(key)
        return self._dict[key]

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


def _kwargtuple_compare(a: Any, b: Any) -> bool:
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


def _convert_str(value: Any) -> Wei:
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
