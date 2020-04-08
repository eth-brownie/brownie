#!/usr/bin/python3

from typing import Dict, List


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


def merge_natspec(devdoc: Dict, userdoc: Dict) -> Dict:
    """
    Merge devdoc and userdoc compiler output to a single dict.

    Arguments
    ---------
    devdoc: dict
        Devdoc compiler output.
    userdoc : dict
        Userdoc compiler output.

    Returns
    -------
    dict
        Combined natspec.
    """
    natspec: Dict = {**{"methods": {}}, **userdoc, **devdoc}
    usermethods = userdoc.get("methods", {})
    devmethods = devdoc.get("methods", {})

    for key in set(list(usermethods) + list(devmethods)):
        try:
            natspec["methods"][key] = {**usermethods.get(key, {}), **devmethods.get(key, {})}
        except TypeError:
            # sometimes Solidity has inconsistent NatSpec formatting ¯\_(ツ)_/¯
            pass
    return natspec
