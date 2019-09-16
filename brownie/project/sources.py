#!/usr/bin/python3

from typing import Dict, Union, Tuple, Any, List
from hashlib import sha1
from pathlib import Path
import re
import textwrap

from brownie.cli.utils import color
from brownie.exceptions import ContractExists


MINIFY_REGEX_PATTERNS = [
    r"(?:\s*\/\/[^\n]*)|(?:\/\*[\s\S]*?\*\/)",  # comments
    r"(?<=\n)\s{1,}|[ \t]{1,}(?=\n)",  # leading / trailing whitespace
    r"(?<=[^\w\s])[ \t]{1,}(?=\w)|(?<=\w)[ \t]{1,}(?=[^\w\s])",  # whitespace between expressions
]

_contract_data: Dict = {}


class Sources:

    """Methods for accessing and manipulating a project's contract source files."""

    def __init__(self, project_path: Union["Path", str, None]) -> None:
        self._source: Dict = {}
        self._contracts: Dict = {}
        if not project_path:
            return
        project_path = Path(project_path)
        for path in project_path.glob("contracts/**/*.sol"):
            if "/_" in path.as_posix():
                continue
            with path.open() as fp:
                source = fp.read()
            path_str: str = path.relative_to(project_path).as_posix()
            self.add(path_str, source)

    def add(self, path: Union["Path", str], source: Any, replace: bool = False) -> None:
        if path in self._source and not replace:
            raise ContractExists(
                f"Contract with path '{path}' already exists in this project."
            )
        data = _get_contract_data(source)
        for name, values in data.items():
            if name in self._contracts and not replace:
                raise ContractExists(
                    f"Contract '{name}' already exists in this project."
                )
            values["path"] = path
        self._source[path] = source
        self._contracts.update(data)

    def get(self, name: str) -> str:
        """Returns the source code file for the given name.

        Args:
            name: contract name or source code path

        Returns: source code as a string."""
        if name in self._contracts:
            return self._source[self._contracts[name]["path"]]
        return self._source[str(name)]

    def get_path_list(self) -> List:
        """Returns a list of source code file paths for the active project."""
        return list(self._source.keys())

    def get_contract_list(self) -> List:
        """Returns a list of contract names for the active project."""
        return list(self._contracts.keys())

    def get_source_path(self, contract_name: str) -> "Path":
        """Returns the path to the source file where a contract is located."""
        return self._contracts[contract_name]["path"]

    def expand_offset(self, contract_name: str, offset: Tuple) -> Tuple:
        """Converts an offset from source with comments removed, to one from the original source."""
        offset_map = self._contracts[contract_name]["offset_map"]

        return (
            offset[0] + next(i[1] for i in offset_map if i[0] <= offset[0]),
            offset[1] + next(i[1] for i in offset_map if i[0] < offset[1]),
        )


def minify(source: str) -> Tuple[str, List]:
    """Given contract source as a string, returns a minified version and an offset map."""
    offsets = [(0, 0)]
    pattern = f"({'|'.join(MINIFY_REGEX_PATTERNS)})"
    for match in re.finditer(pattern, source):
        offsets.append(
            (
                match.start() - offsets[-1][1],
                match.end() - match.start() + offsets[-1][1],
            )
        )
    return re.sub(pattern, "", source), offsets[::-1]


def is_inside_offset(inner: Tuple, outer: Tuple) -> bool:
    """Checks if the first offset is contained in the second offset

    Args:
        inner: inner offset tuple
        outer: outer offset tuple

    Returns: bool"""
    return outer[0] <= inner[0] <= inner[1] <= outer[1]


def get_hash(source: str, contract_name: str, minified: bool) -> str:
    """Returns a hash of the contract source code."""
    if minified:
        source = minify(source)[0]
    try:
        data = _get_contract_data(source)[contract_name]
        offset = slice(*data["offset"])
        return sha1(source[offset].encode()).hexdigest()
    except KeyError:
        return ""


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
        f"{color['dull']}"
        + textwrap.dedent(
            f"{source[pad_start:offset[0]]}{color}"
            f"{source[offset[0]:offset[1]]}{color['dull']}{source[offset[1]:pad_stop]}{color}"
        ),
        "    ",
    )

    count = source[pad_start : offset[0]].count("\n")
    final = final.replace("\n ", f"\n{color['dull']} ", count)
    count = source[offset[0] : offset[1]].count("\n")
    final = final.replace("\n ", f"\n{color} ", count)
    count = source[offset[1] : pad_stop].count("\n")
    final = final.replace("\n ", f"\n{color['dull']} ", count)

    return final, ln


def _get_contract_data(full_source: str) -> Dict:
    key = sha1(full_source.encode()).hexdigest()
    if key in _contract_data:
        return _contract_data[key]
    minified_source, offset_map = minify(full_source)
    minified_key = sha1(minified_source.encode()).hexdigest()
    if minified_key in _contract_data:
        return _contract_data[minified_key]

    contracts = re.findall(
        r"((?:contract|library|interface)[^;{]*{[\s\S]*?})\s*(?=contract|library|interface|$)",
        minified_source,
    )
    data = {}
    for source in contracts:
        type_, name, inherited = re.findall(
            r"\s*(contract|library|interface)\s{1,}(\S*)\s*(?:is\s{1,}(.*?)|)(?:{)",
            source,
        )[0]
        idx = minified_source.index(source)
        offset = (
            idx + next(i[1] for i in offset_map if i[0] <= idx),
            idx
            + len(source)
            + next(i[1] for i in offset_map if i[0] <= idx + len(source)),
        )
        data[name] = {"offset_map": offset_map, "offset": offset}
    _contract_data[key] = data
    _contract_data[minified_key] = data
    return data
