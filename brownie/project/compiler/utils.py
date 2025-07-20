#!/usr/bin/python3

import pathlib
from typing import Dict, Final, List, Optional, Set, Union

from brownie._config import _get_data_folder
from brownie.typing import ContractName


Path: Final = pathlib.Path


def expand_source_map(source_map_str: str | dict) -> List[List]:
    """Expand the compressed sourceMap supplied by solc into a list of lists."""

    if isinstance(source_map_str, dict):
        # NOTE: vyper >= 0.4 gives us a dict that contains the source map
        source_map_str = source_map_str["pc_pos_map_compressed"]
    if not isinstance(source_map_str, str):
        raise TypeError(source_map_str)

    source_map: List = [_expand_row(i) if i else None for i in source_map_str.split(";")]
    for i, value in enumerate(source_map[1:], 1):
        if value is None:
            source_map[i] = source_map[i - 1]
            continue
        for x in range(4):
            if value[x] is None:
                value[x] = source_map[i - 1][x]
    return source_map


def _expand_row(row: str) -> List[Optional[Union[str, int]]]:
    result: List[Optional[Union[str, int]]] = [None] * 4
    # ignore the new "modifier depth" value in solidity 0.6.0
    for i, value in enumerate(row.split(":")[:4]):
        if value:
            result[i] = value if i == 3 else int(value)
    return result


def merge_natspec(
    devdoc: Dict[str, Dict[str, Dict]],
    userdoc: Dict[str, Dict[str, Dict]],
) -> Dict[str, Dict[str, Dict]]:
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
    natspec = {"methods": {}, **userdoc, **devdoc}
    usermethods = userdoc.get("methods", {})
    devmethods = devdoc.get("methods", {})

    keys: Set[str] = set()
    keys.update(usermethods)
    keys.update(devmethods)
    for key in keys:
        try:
            natspec["methods"][key] = {**usermethods.get(key, {}), **devmethods.get(key, {})}
        except TypeError:
            # sometimes Solidity has inconsistent NatSpec formatting ¯\_(ツ)_/¯
            pass
    return natspec


def _get_alias(contract_name: ContractName, path_str: str) -> ContractName:
    # Generate an alias for a contract, used when tracking dependencies.
    # For a contract within the project, the alias == the name. For contracts
    # imported from a dependency, the alias is set as [PACKAGE]/[NAME]
    # to avoid namespace collisions.
    data_path = _get_data_folder().parts
    path_parts = Path(path_str).parts
    if path_parts[: len(data_path)] == data_path:
        idx = len(data_path) + 1
        return f"{path_parts[idx]}/{path_parts[idx+1]}/{contract_name}"  # type: ignore [return-value]
    else:
        return contract_name
