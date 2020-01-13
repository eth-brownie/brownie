#!/usr/bin/python3

import re
from typing import List, Optional

from semantic_version import NpmSpec

from brownie.exceptions import PragmaError


def expand_source_map(source_map_str: str) -> List:
    # Expands the compressed sourceMap supplied by solc into a list of lists
    source_map: List = [_expand_row(i) if i else None for i in source_map_str.split(";")]
    for i, value in enumerate(source_map[1:], 1):
        if value is None:
            source_map[i] = source_map[i - 1]
            continue
        for x in range(4):
            if source_map[i][x] is None:
                source_map[i][x] = source_map[i - 1][x]
    return source_map


def _expand_row(row: str) -> List:
    result: List = [None] * 4
    # ignore the new "modifier depth" value in solidity 0.6.0
    for i, value in enumerate(row.split(":")[:4]):
        if value:
            result[i] = value if i == 3 else int(value)
    return result


def get_pragma_spec(source: str, path: Optional[str] = None) -> NpmSpec:
    pragma_string = next(re.finditer(r"pragma +solidity([^;]*);", source), None)
    if pragma_string is not None:
        return NpmSpec(pragma_string.groups()[0])
    if path:
        raise PragmaError(f"No version pragma in '{path}'")
    raise PragmaError(f"String does not contain a version pragma")
