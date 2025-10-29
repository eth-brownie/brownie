#!/usr/bin/python3

import decimal
from typing import (
    Any,
    Dict,
    Final,
    ItemsView,
    Iterable,
    KeysView,
    List,
    Optional,
    Sequence,
    TypeVar,
    Union,
    final,
    overload,
)

try:
    from vyper.exceptions import DecimalOverrideException
except ImportError:
    DecimalOverrideException = BaseException  # regular catch blocks shouldn't catch

import cchecksum
import faster_eth_utils
from eth_typing import ABIComponent, HexStr
from mypy_extensions import mypyc_attr
from typing_extensions import Self

from brownie._c_constants import Decimal, HexBytes, deepcopy, getcontext
from brownie.utils import bytes_to_hexstring

UNITS: Final = {
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

WeiInputTypes = TypeVar("WeiInputTypes", str, float, int, bytes, decimal.Decimal, None)
# This is no longer used within the codebase but we leave it in place in case downstream users import it

WeiInputType = str | float | int | bytes | decimal.Decimal | None


to_checksum_address: Final = cchecksum.to_checksum_address

add_0x_prefix: Final = faster_eth_utils.add_0x_prefix
is_hex: Final = faster_eth_utils.is_hex
to_bytes: Final = faster_eth_utils.to_bytes


@final
@mypyc_attr(native_class=False)
class Wei(int):
    """Integer subclass that converts a value to wei and allows comparison against
    similarly formatted values.

    Useful for the following formats:
        * a string specifying the unit: "10 ether", "300 gwei", "0.25 shannon"
        * a large float in scientific notation, where direct conversion to int
          would cause inaccuracy: 8.3e32
        * bytes: b'\xff\xff'
        * hex strings: "0x330124\" """

    def __new__(cls, value: WeiInputType) -> Self:
        return int.__new__(cls, _to_wei(value))

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


def _to_wei(value: WeiInputType) -> int:
    original = value
    if isinstance(value, bytes):
        hexstr = HexBytes(value).hex().removeprefix("0x")
        return int(hexstr, 16) if hexstr else 0
    if not value or value == "0x":
        return 0
    if isinstance(value, float) and "e+" in (string := str(value)):
        num_str, dec = string.split("e+")
        num = num_str.split(".") if "." in num_str else [num_str, ""]
        return int(num[0] + num[1][: int(dec)] + "0" * (int(dec) - len(num[1])))
    if not isinstance(value, str):
        return _return_int(original, value)
    elif value.startswith("0x"):
        return int(value, 16)
    for unit, decimals in UNITS.items():
        if f" {unit}" not in value:
            continue
        num_str = value.split(" ")[0]
        num = num_str.split(".") if "." in num_str else [num_str, ""]
        return int(num[0] + num[1][:decimals] + "0" * (decimals - len(num[1])))
    return _return_int(original, value)


def _return_int(original: Any, value: Any) -> int:
    try:
        return int(value)
    except ValueError:
        raise TypeError(f"Cannot convert {type(original).__name__} '{original}' to wei.")


@final
@mypyc_attr(native_class=False)
class Fixed(decimal.Decimal):
    """
    Decimal subclass that allows comparison against strings, integers and Wei.

    Raises TypeError when operations are attempted against floats.
    """

    def __new__(cls, value: Any) -> Self:
        return Decimal.__new__(cls, _to_fixed(value))

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


def _to_fixed(value: Any) -> decimal.Decimal:
    if isinstance(value, float):
        raise TypeError("Cannot convert float to decimal - use a string instead")

    if isinstance(value, (str, bytes)):
        try:
            value = Wei(value)
        except TypeError:
            pass
    try:
        try:
            # until vyper v0.3.1 we can mess with the precision
            ctx = getcontext()
            ctx.prec = 78
        except DecimalOverrideException:
            pass  # vyper set the precision, do nothing.
        return Decimal(value)
    except Exception as e:
        raise TypeError(f"Cannot convert {type(value).__name__} '{value}' to decimal.") from e


@final
@mypyc_attr(native_class=False)
class EthAddress(str):
    """String subclass that raises TypeError when compared to a non-address."""

    def __new__(cls, value: Any) -> Self:
        converted_value: HexStr
        if isinstance(value, str):
            converted_value = value  # type: ignore [assignment]
        elif isinstance(value, bytes):
            converted_value = bytes_to_hexstring(value)
        else:
            converted_value = str(value)  # type: ignore [assignment]
        converted_value = add_0x_prefix(converted_value)
        try:
            converted_value = to_checksum_address(converted_value)
        except ValueError:
            raise ValueError(f"{value!r} is not a valid ETH address") from None
        return str.__new__(cls, converted_value)  # type: ignore

    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, other: Any) -> bool:
        return _address_compare(self, other)

    def __ne__(self, other: Any) -> bool:
        return not _address_compare(self, other)


def _address_compare(a: str, b: Any) -> bool:
    bstr = str(b)
    if not bstr.startswith("0x") or not is_hex(bstr) or len(bstr) != 42:
        raise TypeError(f"Invalid type for comparison: '{bstr}' is not a valid address")
    return a.lower() == bstr.lower()


@final
@mypyc_attr(native_class=False)
class HexString(bytes):
    """Bytes subclass for hexstring comparisons. Raises TypeError if compared to
    a non-hexstring. Evaluates True for hexstrings with the same value but differing
    leading zeros or capitalization."""

    def __new__(cls, value: Any, type_str: str) -> Self:
        return bytes.__new__(cls, _to_bytes(value, type_str))

    def __eq__(self, other: Any) -> bool:
        return _hex_compare(self.hex(), other)

    def __ne__(self, other: Any) -> bool:
        return not _hex_compare(self.hex(), other)

    def __str__(self) -> HexStr:
        return f"0x{self.hex()}"  # type: ignore [return-value]

    def __repr__(self) -> HexStr:
        return str(self)  # type: ignore [return-value]


def _hex_compare(a: str, b: Any) -> bool:
    bstr = str(b)
    if not bstr.startswith("0x") or not is_hex(bstr):
        raise TypeError(f"Invalid type for comparison: '{bstr}' is not a valid hex string")
    return a.lstrip("0x").lower() == bstr.lstrip("0x").lower()


def _to_bytes(value: Any, type_str: str = "bytes32") -> bytes:
    """Convert a value to bytes"""
    if isinstance(value, bool) or not isinstance(value, (bytes, str, int)):
        raise TypeError(f"Cannot convert {type(value).__name__} '{value}' to {type_str}")
    value = _to_hex(value)
    if type_str == "bytes":
        return to_bytes(hexstr=value)
    if type_str == "byte":
        type_str = "bytes1"
    size = int(type_str.strip("bytes"))
    if size < 1 or size > 32:
        raise ValueError(f"Invalid type: {type_str}")
    try:
        return int(value, 16).to_bytes(size, "big")
    except OverflowError:
        raise OverflowError(f"'{value}' exceeds maximum length for {type_str}")


def _to_hex(value: Any) -> HexStr:
    """Convert a value to a hexstring"""
    if isinstance(value, bytes):
        return bytes_to_hexstring(value)
    if isinstance(value, int):
        return hex(value)  # type: ignore [return-value]
    if isinstance(value, str):
        if value in ("", "0x"):
            return "0x00"  # type: ignore [return-value]
        if is_hex(value):
            return add_0x_prefix(value)  # type: ignore [arg-type]
    raise ValueError(f"Cannot convert {type(value).__name__} '{value}' to a hex string")


@final
@mypyc_attr(native_class=False)
class ReturnValue(tuple):
    """Tuple subclass with dict-like functionality, used for iterable return values."""

    _abi: Optional[List[ABIComponent]] = None
    _dict: Dict[str, Any] = {}

    def __new__(
        cls,
        values: Iterable[Any],
        abi: Optional[Sequence[ABIComponent]] = None,
    ) -> "ReturnValue":
        values = list(values)
        for i, value in enumerate(values):
            if isinstance(value, (tuple, list)) and not isinstance(value, ReturnValue):
                if abi is not None and "components" in (value_abi := abi[i]):
                    if value_abi["type"] == "tuple":
                        # tuple
                        values[i] = ReturnValue(value, value_abi["components"])
                    else:
                        # array of tuples
                        inner_abi = value_abi.copy()
                        length = len(value)
                        inner_abi["type"] = inner_abi["type"].rsplit("[", maxsplit=1)[0]
                        final_abi = [deepcopy(inner_abi) for i in range(length)]
                        if inner_abi.get("name"):
                            name = inner_abi["name"]
                            for x in range(length):
                                final_abi[x]["name"] = f"{name}[{x}]"

                        values[i] = ReturnValue(value, final_abi)
                else:
                    # array
                    values[i] = ReturnValue(value)

        self = tuple.__new__(cls, values)
        self._abi = list(abi) if abi else []
        self._dict = {i.get("name", "") or f"arg[{c}]": values[c] for c, i in enumerate(self._abi)}

        return self

    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, other: Any) -> bool:
        return _kwargtuple_compare(self, other)

    def __ne__(self, other: Any) -> bool:
        return not _kwargtuple_compare(self, other)
    
    @overload  # type: ignore [override]
    def __getitem__(self, key: int) -> Any: ...
    @overload
    def __getitem__(self, key: str) -> Any: ...
    @overload
    def __getitem__(
        self,
        key: "slice[Optional[int], Optional[int], Optional[int]]",
    ) -> "ReturnValue": ...
    def __getitem__(
        self,
        key: Union[str, int, "slice[Optional[int], Optional[int], Optional[int]]"],
    ) -> Any:
        if type(key) is slice:
            abi = self._abi
            result = super().__getitem__(key)
            if abi is None:
                return ReturnValue(result)
            item_abi = deepcopy(abi)[key]
            return ReturnValue(result, item_abi)
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

    def dict(self) -> Dict[str, Any]:
        """ReturnValue.dict() -> a dictionary of ReturnValue's named items"""
        response = {}
        for k, v in self._dict.items():
            if isinstance(v, ReturnValue) and v._abi:
                response[k] = v.dict()
            else:
                response[k] = v
        return response

    def index(self, value: Any, start: int = 0, stop: Any = None) -> int:  # type: ignore [override]
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

    def items(self) -> ItemsView[str, Any]:
        """ReturnValue.items() -> a set-like object providing a view on ReturnValue's named items"""
        return self._dict.items()

    def keys(self) -> KeysView[str]:
        """ReturnValue.keys() -> a set-like object providing a view on ReturnValue's keys"""
        return self._dict.keys()


def _kwargtuple_compare(a: Any, b: Any) -> bool:
    if not isinstance(a, (tuple, list, ReturnValue)):
        types_ = {type(a), type(b)}
        if types_.intersection((bool, type(None))):
            return a is b
        if types_.intersection((dict, EthAddress, HexString)):
            return a == b
        return _convert_str(a) == _convert_str(b)
    if not isinstance(b, (tuple, list, ReturnValue)) or len(b) != len(a):
        return False
    return all(_kwargtuple_compare(ai, bi) for ai, bi in zip(a, b))


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
    except (ValueError, TypeError):
        return value
