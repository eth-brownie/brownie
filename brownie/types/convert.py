#!/usr/bin/python3


# format contract inputs based on ABI types
def format_to_abi(abi, inputs):
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
        if type_[-1] == "]":
            # input value is an array, have to check every item
            t, length = type_.rstrip(']').rsplit('[', maxsplit=1)
            if length != "" and len(inputs[i]) != int(length):
                raise ValueError(
                    "'{}': Argument {}, sequence has a ".format(name, i) +
                    "length of {}, should be {}".format(len(inputs[i]), type_)
                    )
            inputs[i] = format_to_abi(
                {'name': name, 'inputs':[{'type': t}] * len(inputs[i])},
                inputs[i]
            )
            continue
        try:
            if "address" in type_:
                inputs[i] = str(inputs[i])
            if "int" in type_:
                inputs[i] = wei(inputs[i])
            elif "bytes" in type_ and type(inputs[i]) is not bytes:
                if type(inputs[i]) is str:
                    if inputs[i][:2] != "0x":
                        inputs[i] = inputs[i].encode()
                    elif type_ != "bytes":
                        inputs[i] = int(inputs[i], 16).to_bytes(int(type_[5:]), "big")
                else:
                    inputs[i] = int(inputs[i]).to_bytes(int(type_[5:]), "big")
        except:
            raise ValueError(
                "'{}': Argument {}, could not convert {} '{}' to type {}".format(
                    name, i, type(inputs[i]).__name__, inputs[i], type_))
    return inputs



def format_output(value):
    if type(value) in (tuple, list):
        return tuple(format_output(i) for i in value)
    elif type(value) is bytes:
        return "0x"+value.hex()
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


UNITS = {
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
