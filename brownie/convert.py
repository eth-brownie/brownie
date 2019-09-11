#!/usr/bin/python3

from copy import deepcopy
import eth_utils
from hexbytes import HexBytes

UNITS = {
    'wei': 0,
    'kwei': 3,
    'babbage': 3,
    'mwei': 6,
    'lovelace': 6,
    'gwei': 9,
    'shannon': 9,
    'microether': 12,
    'szabo': 12,
    'milliether': 15,
    'finney': 15,
    'ether': 18
}


class Wei(int):

    '''Integer subclass that converts a value to wei and allows comparison against
    similarly formatted values.

    Useful for the following formats:
        * a string specifying the unit: "10 ether", "300 gwei", "0.25 shannon"
        * a large float in scientific notation, where direct conversion to int
          would cause inaccuracy: 8.3e32
        * bytes: b'\xff\xff'
        * hex strings: "0x330124"'''

    def __new__(cls, value):
        return super().__new__(cls, _to_wei(value))

    def __hash__(self):
        return super().__hash__()

    def __lt__(self, other):
        return super().__lt__(_to_wei(other))

    def __le__(self, other):
        return super().__le__(_to_wei(other))

    def __eq__(self, other):
        try:
            return super().__eq__(_to_wei(other))
        except TypeError:
            return False

    def __ne__(self, other):
        try:
            return super().__ne__(_to_wei(other))
        except TypeError:
            return True

    def __ge__(self, other):
        return super().__ge__(_to_wei(other))

    def __gt__(self, other):
        return super().__gt__(_to_wei(other))

    def __add__(self, other):
        return Wei(super().__add__(_to_wei(other)))

    def __sub__(self, other):
        return Wei(super().__sub__(_to_wei(other)))


def _to_wei(value):
    original = value
    if value is None:
        return 0
    if type(value) in (bytes, HexBytes):
        value = HexBytes(value).hex()
    if type(value) is float and "e+" in str(value):
        num, dec = str(value).split("e+")
        num = num.split(".") if "." in num else [num, ""]
        return int(num[0] + num[1][:int(dec)] + "0" * (int(dec) - len(num[1])))
    if type(value) is not str:
        return _return_int(original, value)
    if value[:2] == "0x":
        return int(value, 16)
    for unit, dec in UNITS.items():
        if " " + unit not in value:
            continue
        num = value.split(" ")[0]
        num = num.split(".") if "." in num else [num, ""]
        return int(num[0] + num[1][:int(dec)] + "0" * (int(dec) - len(num[1])))
    return _return_int(original, value)


def _return_int(original, value):
    try:
        return int(value)
    except ValueError:
        raise TypeError(f"Could not convert {type(original)} '{original}' to wei.")


def to_uint(value, type_="uint256"):
    '''Convert a value to an unsigned integer'''
    value = Wei(value)
    size = _check_int_size(type_)
    if value < 0 or value >= 2**int(size):
        raise OverflowError(f"{value} is outside allowable range for {type_}")
    return value


def to_int(value, type_="int256"):
    '''Convert a value to a signed integer'''
    value = Wei(value)
    size = _check_int_size(type_)
    if value < -2**int(size) // 2 or value >= 2**int(size) // 2:
        raise OverflowError(f"{value} is outside allowable range for {type_}")
    return value


def _check_int_size(type_):
    size = int(type_.strip("uint") or 256)
    if size < 8 or size > 256 or size // 8 != size / 8:
        raise ValueError(f"Invalid type: {type_}")
    return size


class EthAddress(str):

    '''String subclass that raises TypeError when compared to a non-address.'''

    def __new__(cls, value):
        return super().__new__(cls, to_address(value))

    def __eq__(self, other):
        return _address_compare(str(self), other)

    def __ne__(self, other):
        return not _address_compare(str(self), other)


def _address_compare(a, b):
    b = str(b)
    if not b.startswith('0x') or not eth_utils.is_hex(b) or len(b) != 42:
        raise TypeError(f"Invalid type for comparison: '{b}' is not a valid address")
    return a.lower() == b.lower()


def to_address(value):
    '''Convert a value to an address'''
    if type(value) in (bytes, HexBytes):
        value = HexBytes(value).hex()
    value = eth_utils.add_0x_prefix(str(value))
    try:
        return eth_utils.to_checksum_address(value)
    except ValueError:
        raise ValueError(f"'{value}' is not a valid ETH address.") from None


class HexString(bytes):

    '''Bytes subclass for hexstring comparisons. Raises TypeError if compared to
    a non-hexstring. Evaluates True for hexstrings with the same value but differing
    leading zeros or capitalization.'''

    def __new__(cls, value, type_):
        return super().__new__(cls, to_bytes(value, type_))

    def __eq__(self, other):
        return _hex_compare(self.hex(), other)

    def __ne__(self, other):
        return not _hex_compare(self.hex(), other)

    def __str__(self):
        return "0x" + self.hex()

    def __repr__(self):
        return str(self)


def _hex_compare(a, b):
    b = str(b)
    if not b.startswith('0x') or not eth_utils.is_hex(b):
        raise TypeError(f"Invalid type for comparison: '{b}' is not a valid hex string")
    return a.lstrip('0x').lower() == b.lstrip('0x').lower()


def to_bytes(value, type_="bytes32"):
    '''Convert a value to bytes'''
    if not isinstance(value, (bytes, str, int)):
        raise TypeError(f"'{value}', type {type(value)}, cannot convert to {type_}")
    if type_ == "byte":
        type_ = "bytes1"
    if type_ != "bytes":
        size = int(type_.strip("bytes"))
        if size < 1 or size > 32:
            raise ValueError(f"Invalid type: {type_}")
    else:
        size = float('inf')
    value = bytes_to_hex(value)
    if type_ == "bytes":
        return eth_utils.to_bytes(hexstr=value)
    try:
        return int(value, 16).to_bytes(size, "big")
    except OverflowError:
        raise OverflowError(f"'{value}' exceeds maximum length for {type_}")


def bytes_to_hex(value):
    '''Convert a bytes value to a hexstring'''
    if type(value) not in (bytes, HexBytes, HexString, str, int):
        raise TypeError(f"Cannot convert {type(value)} '{value}' from bytes to hex.")
    if type(value) in (bytes, HexBytes):
        value = HexBytes(value).hex()
    if type(value) is int:
        value = hex(value)
    if not eth_utils.is_hex(value):
        raise ValueError(f"'{value}' is not a valid hex string")
    return eth_utils.add_0x_prefix(value)


def to_bool(value):
    '''Convert a value to a boolean'''
    if type(value) not in (int, float, bool, bytes, HexBytes, str):
        raise TypeError(f"Cannot convert {type(value)} '{value}' to bool")
    if type(value) in (bytes, HexBytes):
        value = HexBytes(value).hex()
    if type(value) is str and value[:2] == "0x":
        value = int(value, 16)
    if value not in (0, 1, True, False):
        raise ValueError(f"Cannot convert {type(value)} '{value}' to bool")
    return bool(value)


def to_string(value):
    '''Convert a value to a string'''
    if type(value) in (bytes, HexBytes):
        value = HexBytes(value).hex()
    value = str(value)
    if value.startswith("0x") and eth_utils.is_hex(value):
        try:
            return eth_utils.to_text(hexstr=value)
        except UnicodeDecodeError as e:
            raise ValueError(e)
    return value


def format_input(abi, inputs):
    '''Format contract inputs based on ABI types.

    Args:
        abi: contract method ABI
        inputs: list of arguments to format

    Returns a list of arguments formatted for use in a Contract tx or call.'''
    if len(inputs) and not len(abi['inputs']):
        raise TypeError(f"{abi['name']} requires no arguments")
    try:
        return _format_abi(abi['inputs'], inputs)
    except Exception as e:
        raise type(e)(f"{abi['name']} {e}") from None


def format_output(abi, outputs):
    '''Format contract outputs based on ABI types.

    Args:
        abi: contract method ABI
        outputs: list of arguments to format

    Returns a list of arguments with standard formatting applied.'''
    return _format_abi(abi['outputs'], outputs)


def format_event(event):
    '''Format event data.

    Args:
        event: decoded event as given by eth_event.decode_logs or eth_event.decode_trace

    Mutates the event in place and returns it.'''

    for e in [i for i in event['data'] if not i['decoded']]:
        e['type'] = "bytes32"
        e['name'] += " (indexed)"
    values = _format_abi(event['data'], [i['value'] for i in event['data']])
    for i in range(len(event['data'])):
        event['data'][i]['value'] = values[i]
    return event


def _format_abi(abi, values):
    '''Apply standard formatting to multiple values of differing types'''
    types = [i['type'] for i in abi]
    values = list(values)
    if len(values) != len(types):
        raise TypeError(f"Expected {len(types)} arguments, got {len(values)}: {','.join(types)}")
    for i, type_ in enumerate(types):
        try:
            if "]" in type_:
                values[i] = _format_array(abi[i], values[i])
            elif type_ == "tuple":
                values[i] = _format_abi(abi[i]['components'], values[i])
            else:
                values[i] = _format_single(type_, values[i])
        except Exception as e:
            raise type(e)(f"argument #{i}: '{values[i]}' - {e}")
    return ReturnValue(values, abi)


def _format_array(abi, values):
    '''Apply standard formatting to multiple values of the same type (arrays)'''
    base_type, length = abi['type'][:-1].rsplit('[', maxsplit=1)
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"Expected sequence, got {type(values)}")
    if length != "" and len(values) != int(length):
        raise ValueError(f"Expected {abi['type']} but sequence has length of {len(values)}")
    if "]" in base_type:
        abi = deepcopy(abi)
        abi['type'] = base_type
        return ReturnValue([_format_array(abi, i) for i in values])
    if base_type == "tuple":
        abi = abi['components']
        return ReturnValue([_format_abi(abi, i) for i in values], abi)
    return ReturnValue([_format_single(base_type, i) for i in values])


def _format_single(type_, value):
    '''Apply standard formatting to a single value'''
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
    '''Tuple subclass with dict-like functionality, used for iterable return values.'''

    def __new__(cls, values, abi=None):
        self = super().__new__(cls, values)
        self._abi = abi or []
        self._dict = {}
        for c, i in enumerate(self._abi):
            if not i['name']:
                continue
            self._dict[i['name']] = values[c]
        return self

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        return _kwargtuple_compare(self, other)

    def __getitem__(self, key):
        if type(key) is slice:
            abi = deepcopy(self._abi)[key]
            result = super().__getitem__(key)
            return ReturnValue(result, abi)
        if isinstance(key, int):
            return super().__getitem__(key)
        return self._dict[key]

    def __contains__(self, value):
        return self.count(value) > 0

    def count(self, value):
        '''ReturnValue.count(value) -> integer -- return number of occurrences of value'''
        count = 0
        for item in self:
            try:
                if _kwargtuple_compare(item, value):
                    count += 1
            except TypeError:
                continue
        return count

    def dict(self):
        '''ReturnValue.dict() -> a dictionary of ReturnValue's named items'''
        return self._dict

    def index(self, value, start=0, stop=None):
        '''ReturnValue.index(value, [start, [stop]]) -> integer -- return first index of value.
        Raises ValueError if the value is not present.'''
        if stop is None:
            stop = len(self)
        for i in range(start, stop):
            try:
                if _kwargtuple_compare(self[i], value):
                    return i
            except TypeError:
                continue
        raise ValueError(f"{value} is not in ReturnValue")

    def items(self):
        '''ReturnValue.items() -> a set-like object providing a view on ReturnValue's named items'''
        return self._dict.items()

    def keys(self):
        '''ReturnValue.keys() -> a set-like object providing a view on ReturnValue's keys'''
        return self._dict.keys()


def _kwargtuple_compare(a, b):
    if type(a) not in (tuple, list, ReturnValue):
        types_ = set([type(a), type(b)])
        if types_.intersection([bool, type(None)]):
            return a is b
        if types_.intersection([dict, EthAddress, HexString]):
            return a == b
        return _convert_str(a) == _convert_str(b)
    if type(b) not in (tuple, list, ReturnValue) or len(b) != len(a):
        return False
    return next((False for i in range(len(a)) if not _kwargtuple_compare(a[i], b[i])), True)


def _convert_str(value):
    if type(value) is not str:
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
