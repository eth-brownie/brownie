import re
from typing import Any, Mapping, Optional, Text

from dotenv.variables import parse_variables


def expand_posix_vars(obj: Any, variables: Mapping[Text, Optional[Any]]) -> Any:
    """expand_posix_vars recursively expands POSIX values in an object.

    Args:
        obj (any): object in which to interpolate variables.
        variables (dict): dictionary that maps variable names to their value
    """
    if isinstance(obj, (dict,)):
        for key, val in obj.items():
            obj[key] = expand_posix_vars(val, variables)
    elif isinstance(obj, (list,)):
        for index in range(len(obj)):
            obj[index] = expand_posix_vars(obj[index], variables)
    elif isinstance(obj, (str,)):
        obj = _str_to_python_value(_expand(obj, variables))
    return obj


def _expand(value, variables={}):
    """_expand does POSIX-style variable expansion

    This is adapted from python-dotenv, specifically here:

    https://github.com/theskumar/python-dotenv/commit/17dba65244c1d4d10f591fe37c924bd2c6fd1cfc

    We need this layer here so we can explicitly pass in variables;
    python-dotenv assumes you want to use os.environ.
    """

    if not isinstance(value, (str,)):
        return value
    atoms = parse_variables(value)
    return "".join([str(atom.resolve(variables)) for atom in atoms])


INT_REGEX = re.compile(r"^[-+]?[0-9]+$")


def _str_to_python_value(val):
    """_str_to_python_value infers the data type from a string.

    This could eventually use PyYAML's parsing logic.
    """
    if not isinstance(val, (str,)):
        return val
    elif val == "true" or val == "True" or val == "on":
        return True
    elif val == "false" or val == "False" or val == "off":
        return False
    elif INT_REGEX.match(val):
        return int(val)
    return val
