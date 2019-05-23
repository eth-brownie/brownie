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


def _check_int_size(type_):
    size = int(type_.strip("uint") or 256)
    if size < 8 or size > 256 or size // 8 != size / 8:
        raise ValueError("Invalid type: {}".format(type_))
    return size


def to_uint(value, type_="uint256"):
    '''Convert a value to an unsigned integer'''
    value = wei(value)
    size = _check_int_size(type_)
    if value < 0 or value >= 2**int(size):
        raise OverflowError("{} is outside allowable range for {}".format(value, type_))
    return value


def to_int(value, type_="int256"):
    '''Convert a value to a signed integer'''
    value = wei(value)
    size = _check_int_size(type_)
    if value < -2**int(size) // 2 or value >= 2**int(size) // 2:
        raise OverflowError("{} is outside allowable range for {}".format(value, type_))
    return value


def to_bool(value):
    '''Convert a value to a boolean'''
    if type(value) not in (int, float, bool, bytes, HexBytes, str):
        raise TypeError("Cannot convert {} '{}' to bool".format(type(value), value))
    if type(value) in (bytes, HexBytes):
        value = HexBytes(value).hex()
    if type(value) is str and value[:2] == "0x":
        value = int(value, 16)
    if value not in (0, 1, True, False):
        raise ValueError("Cannot convert {} '{}' to bool".format(type(value), value))
    return bool(value)


def to_address(value):
    '''Convert a value to an address'''
    if type(value) in (bytes, HexBytes):
        value = HexBytes(value).hex()
    value = eth_utils.add_0x_prefix(str(value))
    try:
        return eth_utils.to_checksum_address(value)
    except ValueError:
        raise ValueError("'{}' is not a valid ETH address.".format(value))


def to_bytes(value, type_="bytes32"):
    '''Convert a value to bytes'''
    if type(value) not in (HexBytes, bytes, str, int):
        raise TypeError("'{}', type {}, cannot convert to {}".format(value, type(value), type_))
    if type_ == "byte":
        type_ = "bytes1"
    if type_ != "bytes":
        size = int(type_.strip("bytes"))
        if size < 1 or size > 32:
            raise ValueError("Invalid type: {}".format(type_))
    else:
        size = float('inf')
    value = bytes_to_hex(value)
    if type_ == "bytes":
        return eth_utils.to_bytes(hexstr=value)
    try:
        return int(value, 16).to_bytes(size, "big")
    except OverflowError:
        raise OverflowError("'{}' exceeds maximum length for {}".format(value, type_))


def to_string(value):
    '''Convert a value to a string'''
    if type(value) in (bytes, HexBytes):
        value = HexBytes(value).hex()
    value = str(value)
    if value.startswith('0x') and eth_utils.is_hex(value):
        try:
            return eth_utils.to_text(hexstr=value)
        except UnicodeDecodeError as e:
            raise ValueError(e)
    return value


def wei(value):
    '''Converts a value to wei.

    Useful for the following formats:
        * a string specifying the unit: "10 ether", "300 gwei", "0.25 shannon"
        * a large float in scientific notation, where direct conversion to int
          would cause inaccuracy: 8.3e32
        * bytes: b'\xff\xff'
        * hex strings: "0x330124"'''
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
        return int(value)
    if value[:2] == "0x":
        return int(value, 16)
    for unit, dec in UNITS.items():
        if " " + unit not in value:
            continue
        num = value.split(" ")[0]
        num = num.split(".") if "." in num else [num, ""]
        return int(num[0] + num[1][:int(dec)] + "0" * (int(dec) - len(num[1])))
    try:
        return int(value)
    except ValueError:
        raise TypeError("Could not convert {} '{}' to wei.".format(type(original), original))


def bytes_to_hex(value):
    '''Convert a bytes value to a hexstring'''
    if type(value) not in (bytes, HexBytes, str, int):
        raise TypeError("Cannot convert {} '{}' from bytes to hex.".format(type(value), value))
    if type(value) in (bytes, HexBytes):
        value = HexBytes(value).hex()
    if type(value) is int:
        value = hex(value)
    if not eth_utils.is_hex(value):
        raise ValueError("'{}' is not a valid hex string".format(value))
    return eth_utils.add_0x_prefix(value)


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


def _format(abi, key, values):
    try:
        name = abi['name']
        types = [i['type'] for i in abi[key]]
    except Exception:
        raise InvalidABI("ABI must be a dictionary with name and {} values.".format(key))
    values = list(values)
    if len(values) and not len(types):
        raise TypeError("{} requires no arguments".format(name))
    if len(values) != len(types):
        raise TypeError("{} requires {} arguments ({} given): {}".format(
            name, len(types), len(values), ",".join(types)
        ))
    for i, type_ in enumerate(types):
        if ']' in type_:
            # input value is an array, have to check every item
            base_type, length = type_[:-1].rsplit('[', maxsplit=1)
            if type(values[i]) not in (list, tuple):
                raise TypeError(
                    "{} argument #{} is type '{}' - given value "
                    "must be a list or tuple".format(name, i, type_)
                )
            if length != "" and len(values[i]) != int(length):
                raise ValueError(
                    "{} argument #{}, sequence has a ".format(name, i) +
                    "length of {}, should be {}".format(len(values[i]), type_)
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
            elif "bool" in type_:
                values[i] = to_bool(values[i])
            elif "address" in type_:
                values[i] = to_address(values[i])
            elif "byte" in type_:
                if key == "inputs":
                    values[i] = to_bytes(values[i], type_)
                else:
                    values[i] = bytes_to_hex(values[i])
            elif "string" in type_:
                values[i] = to_string(values[i])
        except Exception as e:
            raise type(e)("{} argument #{}: '{}' - {}".format(name, i, values[i], e))
    return tuple(values)
