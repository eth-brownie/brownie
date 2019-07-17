#!/usr/bin/python3

import eth_utils
from hexbytes import HexBytes

from brownie.exceptions import InvalidABI

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


class HexString(str):

    '''String subclass for hexstring comparisons. Raises TypeError if compared to
    a non-hexstring. Evaluates True for hexstrings with the same value but differing
    leading zeros or capitalization.'''

    def __new__(cls, value):
        return super().__new__(cls, bytes_to_hex(value))

    def __eq__(self, other):
        return _hex_compare(self, other)

    def __ne__(self, other):
        return not _hex_compare(self, other)


def _hex_compare(a, b):
    b = str(b)
    if not b.startswith('0x') or not eth_utils.is_hex(b):
        raise TypeError(f"Invalid type for comparison: '{b}' is not a valid hex string")
    return a.lstrip('0x').lower() == b.lstrip('0x').lower()


def to_bytes(value, type_="bytes32"):
    '''Convert a value to bytes'''
    if type(value) not in (HexBytes, HexString, bytes, str, int):
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
    return _format(abi, "inputs", inputs)


def format_output(abi, outputs):
    '''Format contract outputs based on ABI types.

    Args:
        abi: contract method ABI
        outputs: list of arguments to format

    Returns a list of arguments with standard formatting applied.'''
    return _format(abi, "outputs", outputs)


def format_event(event):
    '''Format event data.

    Args:
        event: decoded event as given by eth_event.decode_logs or eth_event.decode_trace

    Mutates the event in place and returns it.'''

    for e in [i for i in event['data'] if not i['decoded']]:
        e['type'] = "bytes32"
        e['name'] += " (indexed)"
    values = _format(event, 'data', [i['value'] for i in event['data']])
    for i in range(len(event['data'])):
        event['data'][i]['value'] = values[i]
    return event


def _format(abi, key, values):
    try:
        name = abi['name']
        types = [i['type'] for i in abi[key]]
    except Exception:
        raise InvalidABI(f"ABI must be a dictionary with name and {key} values.")
    values = list(values)
    if len(values) and not len(types):
        raise TypeError(f"{name} requires no arguments")
    if len(values) != len(types):
        raise TypeError(
            f"{name} requires {len(types)} arguments ({len(values)} given): {','.join(types)}"
        )
    for i, type_ in enumerate(types):
        if "]" in type_:
            # input value is an array, have to check every item
            base_type, length = type_[:-1].rsplit('[', maxsplit=1)
            if type(values[i]) not in (list, tuple):
                raise TypeError(
                    f"{name} argument #{i} is type '{type_}' - given value must be a list or tuple"
                )
            if length != "" and len(values[i]) != int(length):
                raise ValueError(
                    f"{name} argument #{i}, sequence has {len(values[i])} items, should be {type_}"
                )
            values[i] = _format(
                {'name': name, key: [{'type': base_type}] * len(values[i])},
                key,
                values[i]
            )
            continue
        try:
            if "uint" in type_:
                values[i] = to_uint(values[i], type_)
            elif "int" in type_:
                values[i] = to_int(values[i], type_)
            elif type_ == "bool":
                values[i] = to_bool(values[i])
            elif type_ == "address":
                if key == "inputs":
                    values[i] = to_address(values[i])
                else:
                    values[i] = EthAddress(values[i])
            elif "byte" in type_:
                if key == "inputs":
                    values[i] = to_bytes(values[i], type_)
                else:
                    values[i] = HexString(values[i])
            elif "string" in type_:
                values[i] = to_string(values[i])
            else:
                raise TypeError(f"Unknown type: {type_}")
        except Exception as e:
            raise type(e)(f"{name} argument #{i}: '{values[i]}' - {e}")
    return tuple(values)
