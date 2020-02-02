#!/usr/bin/python3

import json
import re
import textwrap
from hashlib import sha1
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from semantic_version import NpmSpec

from brownie.exceptions import NamespaceCollision, PragmaError, UnsupportedLanguage
from brownie.utils import color

SOLIDITY_MINIFY_REGEX = [
    r"(?:\s*\/\/[^\n]*)|(?:\/\*[\s\S]*?\*\/)",  # comments
    r"(?<=\n)\s+|[ \t]+(?=\n)",  # leading / trailing whitespace
    r"(?<=[^\w\s])[ \t]+(?=\w)|(?<=\w)[ \t]+(?=[^\w\s])",  # whitespace between expressions
]

VYPER_MINIFY_REGEX = [
    r"((\n|^)[\s]*?#[\s\S]*?)(?=\n[^#])",
    r'([\s]*?"""[\s\S]*?""")(?=\n)',
    r"([\s]*?'''[\s\S]*?''')(?=\n)",
    r"(\n)(?=\n)",
]

_contract_data: Dict = {}


class Sources:

    """Methods for accessing and manipulating a project's contract source files."""

    def __init__(self, contract_sources: Dict, interface_sources: Dict) -> None:
        self._source: Dict = {}
        self._contracts: Dict = {}
        self._interfaces: Dict = {}

        collisions: Dict = {}
        for path, source in contract_sources.items():
            self._source[path] = source
            data = _get_contract_data(source, path)
            for name, values in data.items():
                if name in self._contracts:
                    collisions.setdefault(name, set()).update([path, self._contracts[name]["path"]])
                values["path"] = path
            self._contracts.update(data)

        for path, source in interface_sources.items():
            self._source[path] = source
            if Path(path).suffix != ".sol":
                data = {Path(path).stem: minify(source, Path(path).suffix)[0]}
            else:
                data = get_contracts(minify(source, "Solidity")[0])
            for name, source in data.items():
                if name in self._contracts:
                    collisions.setdefault(name, set()).update([path, self._contracts[name]["path"]])
                if name in self._interfaces:
                    collisions.setdefault(name, set()).update(
                        [path, self._interfaces[name]["path"]]
                    )
                self._interfaces[name] = {"path": path, "hash": sha1(source.encode()).hexdigest()}

        if collisions:
            raise NamespaceCollision(
                f"Multiple contracts or interfaces with the same name\n  "
                + "\n  ".join(f"{k}: {', '.join(sorted(v))}" for k, v in collisions.items())
            )

    def get(self, name: str) -> str:
        """Returns the source code file for the given name.

        Args:
            name: contract name or source code path

        Returns: source code as a string."""
        if name in self._contracts:
            return self._source[self._contracts[name]["path"]]
        return self._source[str(name)]

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
        return {k: v["hash"] for k, v in self._interfaces.items()}

    def get_interface_sources(self) -> Dict:
        """Returns a dict of interfaces sources in the form {path: source}"""
        return {v["path"]: self._source[v["path"]] for v in self._interfaces.values()}

    def get_source_path(self, contract_name: str) -> str:
        """Returns the path to the source file where a contract is located."""
        if contract_name in self._contracts:
            return self._contracts[contract_name]["path"]
        if contract_name in self._interfaces:
            return self._interfaces[contract_name]["path"]
        raise KeyError(contract_name)

    def expand_offset(self, contract_name: str, offset: Tuple) -> Tuple:
        """Converts an offset from source with comments removed, to one from the original source."""
        offset_map = self._contracts[contract_name]["offset_map"]

        return (
            offset[0] + next(i[1] for i in offset_map if i[0] <= offset[0]),
            offset[1] + next(i[1] for i in offset_map if i[0] < offset[1]),
        )


def minify(source: str, language: str = "Solidity") -> Tuple[str, List]:
    """Given source as a string, returns a minified version and an offset map."""
    offsets = [(0, 0)]
    if language.lower() in ("json", ".json"):
        abi = json.loads(source)
        return json.dumps(abi, sort_keys=True, separators=(",", ":"), default=str), []
    if language.lower() in ("solidity", ".sol"):
        pattern = f"({'|'.join(SOLIDITY_MINIFY_REGEX)})"
    elif language.lower() in ("vyper", ".vy"):
        pattern = f"({'|'.join(VYPER_MINIFY_REGEX)})"
    else:
        raise UnsupportedLanguage(language)
    for match in re.finditer(pattern, source):
        offsets.append(
            (match.start() - offsets[-1][1], match.end() - match.start() + offsets[-1][1])
        )
    return re.sub(pattern, "", source), offsets[::-1]


def is_inside_offset(inner: Tuple, outer: Tuple) -> bool:
    """Checks if the first offset is contained in the second offset

    Args:
        inner: inner offset tuple
        outer: outer offset tuple

    Returns: bool"""
    return outer[0] <= inner[0] <= inner[1] <= outer[1]


def get_hash(source: str, contract_name: str, minified: bool, language: str) -> str:
    """Returns a hash of the contract source code."""
    if minified:
        source = minify(source, language)[0]
    if language.lower() == "solidity":
        try:
            source = get_contracts(source)[contract_name]
        except KeyError:
            return ""
    return sha1(source.encode()).hexdigest()


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


def _get_contract_data(full_source: str, path_str: str) -> Dict:
    key = sha1(full_source.encode()).hexdigest()
    if key in _contract_data:
        return _contract_data[key]

    path = Path(path_str)
    minified_source, offset_map = minify(full_source, path.suffix)

    if path.suffix == ".vy":
        data = {path.stem: {"offset": (0, len(full_source)), "offset_map": offset_map}}
    else:
        data = {}
        for name, source in get_contracts(minified_source).items():
            idx = minified_source.index(source)
            offset = (
                idx + next(i[1] for i in offset_map if i[0] <= idx),
                idx + len(source) + next(i[1] for i in offset_map if i[0] <= idx + len(source)),
            )
            data[name] = {"offset_map": offset_map, "offset": offset}
    _contract_data[key] = data
    return data


def get_contracts(full_source: str) -> Dict:

    """
    Extracts code for individual contracts from a complete Solidity source

    Args:
        full_source: Solidity source code

    Returns: dict of {"ContractName": "source"}
    """

    data = {}
    contracts = re.findall(
        r"((?:abstract contract|contract|library|interface)\s[^;{]*{[\s\S]*?})\s*(?=(?:abstract contract|contract|library|interface)\s|$)",  # NOQA: E501
        full_source,
    )
    for source in contracts:
        type_, name, inherited = re.findall(
            r"(abstract contract|contract|library|interface)\s+(\S*)\s*(?:is\s+([\s\S]*?)|)(?:{)",
            source,
        )[0]
        data[name] = source
    return data


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
