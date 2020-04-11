#!/usr/bin/python3

import re
import textwrap
from hashlib import sha1
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from semantic_version import NpmSpec

from brownie.exceptions import NamespaceCollision, PragmaError
from brownie.utils import color


class Sources:

    """Methods for accessing and manipulating a project's contract source files."""

    def __init__(self, contract_sources: Dict, interface_sources: Dict) -> None:
        self._source: Dict = {}
        self._contracts: Dict = {}
        self._interfaces: Dict = {}

        collisions: Dict = {}
        for path, source in contract_sources.items():
            self._source[path] = source
            if Path(path).suffix != ".sol":
                contract_names = [Path(path).stem]
            else:
                contract_names = get_contract_names(source)
            for name in contract_names:
                if name in self._contracts:
                    collisions.setdefault(name, set()).update([path, self._contracts[name]])
                self._contracts[name] = path

        for path, source in interface_sources.items():
            self._source[path] = source

            if Path(path).suffix != ".sol":
                interface_names = [Path(path).stem]
            else:
                interface_names = get_contract_names(source)
            for name in interface_names:
                if name in self._contracts:
                    collisions.setdefault(name, set()).update([path, self._contracts[name]])
                if name in self._interfaces:
                    collisions.setdefault(name, set()).update([path, self._interfaces[name]])
                self._interfaces[name] = path

        if collisions:
            raise NamespaceCollision(
                f"Multiple contracts or interfaces with the same name\n  "
                + "\n  ".join(f"{k}: {', '.join(sorted(v))}" for k, v in collisions.items())
            )

    def get(self, key: str) -> str:
        """
        Return the source code file for the given name.

        Args:
            key: contract name or source code path

        Returns: source code as a string."""
        key = str(key)

        if key in self._contracts:
            return self._source[self._contracts[key]]

        if key not in self._source:
            # for sources outside this project (packages, other projects)
            with Path(key).open() as fp:
                source = fp.read()
                self._source[key] = source

        return self._source[key]

    def get_path_list(self) -> List:
        """Returns a sorted list of source code file paths for the active project."""
        return sorted(self._source.keys())

    def get_contract_list(self) -> List:
        """Returns a sorted list of contract names for the active project."""
        return sorted(self._contracts.keys())

    def get_interface_list(self) -> List:
        """Returns a sorted list of interface names for the active project."""
        return sorted(self._interfaces.keys())

    def get_interface_hashes(self) -> Dict:
        """Returns a dict of interface hashes in the form of {name: hash}"""
        return {k: sha1(self._source[v].encode()).hexdigest() for k, v in self._interfaces.items()}

    def get_interface_sources(self) -> Dict:
        """Returns a dict of interfaces sources in the form {path: source}"""
        return {v: self._source[v] for v in self._interfaces.values()}

    def get_source_path(self, contract_name: str) -> str:
        """Returns the path to the source file where a contract is located."""
        if contract_name in self._contracts:
            return self._contracts[contract_name]
        if contract_name in self._interfaces:
            return self._interfaces[contract_name]
        raise KeyError(contract_name)


def is_inside_offset(inner: Tuple, outer: Tuple) -> bool:
    """Checks if the first offset is contained in the second offset

    Args:
        inner: inner offset tuple
        outer: outer offset tuple

    Returns: bool"""
    return outer[0] <= inner[0] <= inner[1] <= outer[1]


def highlight_source(source: str, offset: Tuple, pad: int = 3) -> Tuple:
    """Returns a highlighted section of source code.

    Args:
        path: Path to the source
        offset: Tuple of (start offset, stop offset)
        pad: Number of unrelated lines of code to include before and after

    Returns:
        str: Highlighted source code
        int: Line number that highlight begins on"""

    newlines = [i for i in range(len(source)) if source[i] == "\n"]
    try:
        pad_start = newlines.index(next(i for i in newlines if i >= offset[0]))
        pad_stop = newlines.index(next(i for i in newlines if i >= offset[1]))
    except StopIteration:
        return None, None

    ln = (pad_start + 1, pad_stop + 1)
    pad_start = newlines[max(pad_start - (pad + 1), 0)]
    pad_stop = newlines[min(pad_stop + pad, len(newlines) - 1)]

    final = textwrap.indent(
        f"{color('dark white')}"
        + textwrap.dedent(
            f"{source[pad_start:offset[0]]}{color}"
            f"{source[offset[0]:offset[1]]}{color('dark white')}{source[offset[1]:pad_stop]}{color}"
        ),
        "    ",
    )

    count = source[pad_start : offset[0]].count("\n")
    final = final.replace("\n ", f"\n{color('dark white')} ", count)
    count = source[offset[0] : offset[1]].count("\n")
    final = final.replace("\n ", f"\n{color} ", count)
    count = source[offset[1] : pad_stop].count("\n")
    final = final.replace("\n ", f"\n{color('dark white')} ", count)

    return final, ln


def get_contract_names(full_source: str) -> List:
    """
    Get contract names from Solidity source code.

    Args:
        full_source: Solidity source code

    Returns: list of contract names
    """
    # remove comments in case they contain code snippets that could fail the regex
    comment_regex = r"(?:\s*\/\/[^\n]*)|(?:\/\*[\s\S]*?\*\/)"
    uncommented_source = re.sub(comment_regex, "", full_source)
    contracts = re.findall(
        r"((?:abstract contract|contract|library|interface)\s[^;{]*{[\s\S]*?})\s*(?=(?:abstract contract|contract|library|interface)\s|$)",  # NOQA: E501
        uncommented_source,
    )

    contract_names = []
    for source in contracts:
        _, name, _ = re.findall(
            r"(abstract contract|contract|library|interface)\s+(\S*)\s*(?:is\s+([\s\S]*?)|)(?:{)",
            source,
        )[0]
        contract_names.append(name)
    return contract_names


def get_pragma_spec(source: str, path: Optional[str] = None) -> NpmSpec:

    """
    Extracts pragma information from Solidity source code.

    Args:
        source: Solidity source code
        path: Optional path to the source (only used for error reporting)

    Returns: NpmSpec object
    """

    pragma_match = next(re.finditer(r"pragma +solidity([^;]*);", source), None)
    if pragma_match is not None:
        pragma_string = pragma_match.groups()[0]
        pragma_string = " ".join(pragma_string.split())
        return NpmSpec(pragma_string)
    if path:
        raise PragmaError(f"No version pragma in '{path}'")
    raise PragmaError(f"String does not contain a version pragma")
