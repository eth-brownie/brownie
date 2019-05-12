#!/usr/bin/python3

import eth_utils
from hexbytes import HexBytes

UNITS = {
    'wei': 1,
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


def format_input(abi, inputs):
    '''Format contract inputs based on ABI types.

    Args:
        abi: contract method ABI
        inputs: list of arguments to format

    Returns a list of arguments formatted for use in a Contract tx or call.'''
    name = abi['name']
    types = [i['type'] for i in abi['inputs']]
    inputs = list(inputs)
    if len(inputs) and not len(types):
        raise AttributeError("{} requires no arguments".format(name))
    if len(inputs) != len(types):
        raise AttributeError("{} requires the following arguments: {}".format(
            name, ",".join(types)
        ))
    for i, type_ in enumerate(types):
        if ']' in type_:
            # input value is an array, have to check every item
            base_type, length = type_[:-1].rsplit('[', maxsplit=1)
            if length != "" and len(inputs[i]) != int(length):
                raise ValueError(
                    "'{}': Argument {}, sequence has a ".format(name, i) +
                    "length of {}, should be {}".format(len(inputs[i]), type_)
                    )
            inputs[i] = format_input(
                {'name': name, 'inputs': [{'type': base_type}] * len(inputs[i])},
                inputs[i]
            )
            continue
        try:
            if "uint" in type_:
                inputs[i] = to_uint(inputs[i], type_)
            elif "int" in type_:
                inputs[i] = to_int(inputs[i], type_)
            elif "bool" in type_:
                inputs[i] = to_bool(inputs[i])
            elif "address" in type_:
                inputs[i] = to_address(inputs[i])
            elif "bytes" in type_:
                inputs[i] = to_bytes(inputs[i], type_)
            elif "string" in type_:
                inputs[i] = to_string(inputs[i])
        except Exception as e:
            raise type(e)('{}: Argument {}, {}'.format(name, i, e))
    return inputs


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
    if value not in (0, 1, True, False):
        raise TypeError("Cannot convert {} '{}' to bool".format(type(value), value))
    return bool(value)


def to_address(value):
    '''Convert a value to an address'''
    if type(value) is bytes:
        value = value.hex()
    value = eth_utils.add_0x_prefix(str(value))
    try:
        return eth_utils.to_checksum_address(value)
    except ValueError:
        raise ValueError("{} is not a valid ETH address.".format(value))


def to_bytes(value, type_="bytes32"):
    '''Convert a value to bytes'''
    if type(value) not in (bytes, str, int):
        raise TypeError("'{}', type {}, cannot convert to {}".format(value, type(value), type_))
    if type_ == "byte":
        type_ = "bytes1"
    if type_ != "bytes":
        size = int(type_.strip("bytes"))
        if size < 1 or size > 32:
            raise ValueError("Invalid type: {}".format(type_))
    else:
        size = float('inf')
    if type(value) is bytes:
        if len(eth_utils.to_hex(value)) - 2 > size:
            raise OverflowError("{} exceeds maximum length for {}".format(value, type_))
        return value
    if type(value) is int:
        value = hex(value)
    if not eth_utils.is_hex(value):
        raise ValueError("{} is not a valid hex string, cannot convert to {}".format(value, type_))
    value = eth_utils.add_0x_prefix(value)
    if type_ == "bytes":
        return eth_utils.to_bytes(hexstr=value)
    try:
        return int(value, 16).to_bytes(size, "big")
    except OverflowError:
        raise OverflowError("{} exceeds maximum length for {}".format(value, type_))


def to_string(value):
    '''Convert a value to a string'''
    value = str(value)
    if eth_utils.is_hex(value):
        value = eth_utils.to_text(value)
    return value


def format_output(value):
    '''Converts output from a contract call into a more human-readable format.'''
    if type(value) in (tuple, list):
        return tuple(format_output(i) for i in value)
    elif type(value) is bytes:
        return "0x"+value.hex()
    elif type(value) is HexBytes:
        return value.hex()
    return value


def wei(value):
    '''Converts a value to wei.

    Useful for the following formats:
        * a string specifying the unit: "10 ether", "300 gwei", "0.25 shannon"
        * a large float in scientific notation, where direct conversion to int
          would cause inaccuracy: 8.3e32
        * bytes: b'\xff\xff'
        * hex strings: "0x330124"'''
    if value is None:
        return 0
    if type(value) is bytes:
        value = "0x"+value.hex()
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
        raise ValueError("Unknown denomination: {}".format(value))
