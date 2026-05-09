#!/usr/bin/python3

import io
import textwrap
from tokenize import COMMENT, TokenError, tokenize
from typing import Final, final

from eth_typing import HexStr

from brownie._c_constants import Path, regex_findall, regex_finditer, regex_sub, sha1
from brownie._versioning import SolidityPragmaSpec, VyperPragmaSpec
from brownie.exceptions import NamespaceCollision, PragmaError
from brownie.typing import ContractName, Offset
from brownie.utils import color
from brownie.utils._color import dark_white


@final
class Sources:
    """Methods for accessing and manipulating a project's contract source files."""

    def __init__(self, contract_sources: dict[str, str], interface_sources: dict[str, str]) -> None:
        self._contract_sources: Final[dict[str, str]] = {}
        self._contracts: Final[dict[ContractName, str]] = {}
        self._interface_sources: Final[dict[str, str]] = {}
        self._interfaces: Final[dict[ContractName, str]] = {}

        contracts: dict[ContractName, tuple[str, str]] = {}
        collisions: dict[ContractName, set[str]] = {}
        contract_names: list[tuple[ContractName, str]]
        for path, source in contract_sources.items():
            self._contract_sources[path] = source
            if Path(path).suffix != ".sol":
                contract_names = [(Path(path).stem, "contract")]  # type: ignore [list-item]
            else:
                contract_names = get_contract_names(source)
            for name, type_ in contract_names:
                if name in contracts:
                    if type_ == "interface":
                        # allow names to overlap when dealing with interfaces
                        continue
                    if contracts[name][1] != "interface":
                        collisions.setdefault(name, set()).update([path, contracts[name][0]])
                contracts[name] = (path, type_)

        for k, v in contracts.items():
            self._contracts[k] = v[0]

        interface_names: list[tuple[ContractName, str]]
        for path, source in interface_sources.items():
            self._interface_sources[path] = source

            if Path(path).suffix != ".sol":
                interface_names = [(Path(path).stem, "interface")]  # type: ignore [list-item]
            else:
                interface_names = get_contract_names(source)
            for name, type_ in interface_names:
                if name in self._interfaces:
                    collisions.setdefault(name, set()).update([path, self._interfaces[name]])
                self._interfaces[name] = path

        if collisions:
            raise NamespaceCollision(
                "Multiple contracts or interfaces with the same name\n  "
                + "\n  ".join(f"{k}: {', '.join(sorted(v))}" for k, v in collisions.items())
            )

    def get(self, key: ContractName | str) -> str:
        """
        Return the source code file for the given name.

        Args:
            key: contract name or source code path

        Returns: source code as a string."""
        key = str(key)

        if key in self._contracts:
            return self._contract_sources[self._contracts[key]]  # type: ignore [index]
        if key in self._contract_sources:
            return self._contract_sources[key]
        if key in self._interface_sources:
            return self._interface_sources[key]

        # for sources outside this project (packages, other projects)
        with Path(key).open() as fp:
            source = fp.read()
            self._contract_sources[key] = source
            return source

    def get_path_list(self) -> list[str]:
        """Returns a sorted list of source code file paths for the active project."""
        return sorted(self._contract_sources.keys())

    def get_contract_list(self) -> list[ContractName]:
        """Returns a sorted list of contract names for the active project."""
        return sorted(self._contracts.keys())

    def get_interface_list(self) -> list[ContractName]:
        """Returns a sorted list of interface names for the active project."""
        return sorted(self._interfaces.keys())

    def get_interface_hashes(self) -> dict[ContractName, HexStr]:
        """Returns a dict of interface hashes in the form of {name: hash}"""
        return {
            k: sha1(self._interface_sources[v].encode()).hexdigest()  # type: ignore [misc]
            for k, v in self._interfaces.items()
        }

    def get_interface_sources(self) -> dict[str, str]:
        """Returns a dict of interfaces sources in the form {path: source}"""
        return {v: self._interface_sources[v] for v in self._interfaces.values()}

    def get_source_path(self, contract_name: ContractName, is_interface: bool = False) -> str:
        """Returns the path to the source file where a contract is located."""
        if contract_name in self._contracts and not is_interface:
            return self._contracts[contract_name]
        if contract_name in self._interfaces:
            return self._interfaces[contract_name]
        raise KeyError(contract_name)


def is_inside_offset(inner: Offset, outer: Offset) -> bool:
    """Checks if the first offset is contained in the second offset

    Args:
        inner: inner offset tuple
        outer: outer offset tuple

    Returns: bool"""
    return outer[0] <= inner[0] <= inner[1] <= outer[1]


def highlight_source(
    source: str, offset: Offset, pad: int = 3
) -> tuple[str | None, tuple[int, int] | None]:
    """Returns a highlighted section of source code.

    Args:
        path: Path to the source
        offset: Tuple of (start offset, stop offset)
        pad: Number of unrelated lines of code to include before and after

    Returns:
        str: Highlighted source code
        int: Line number that highlight begins on"""

    newlines = [i for i in range(len(source)) if source[i] == "\n"]
    start_offset, stop_offset = offset
    try:
        pad_start = newlines.index(next(i for i in newlines if i >= start_offset))
        pad_stop = newlines.index(next(i for i in newlines if i >= stop_offset))
    except StopIteration:
        return None, None

    ln = (pad_start + 1, pad_stop + 1)
    pad_start = newlines[max(pad_start - (pad + 1), 0)]
    pad_stop = newlines[min(pad_stop + pad, len(newlines) - 1)]

    dedented = textwrap.dedent(
        f"{source[pad_start:start_offset]}{color}"
        f"{source[start_offset:stop_offset]}{dark_white}{source[stop_offset:pad_stop]}{color}"
    )
    final = textwrap.indent(f"{dark_white}{dedented}", "    ")

    count = source[pad_start:start_offset].count("\n")
    final = final.replace("\n ", f"\n{dark_white} ", count)
    count = source[start_offset:stop_offset].count("\n")
    final = final.replace("\n ", f"\n{color} ", count)
    count = source[stop_offset:pad_stop].count("\n")
    final = final.replace("\n ", f"\n{dark_white} ", count)

    # prepend with a newline if the offset starts on the first line
    if start_offset < newlines[1]:
        final = f"\n{final}"

    return final, ln


def get_contract_names(full_source: str) -> list[tuple[ContractName, str]]:
    """
    Get contract names from Solidity source code.

    Args:
        full_source: Solidity source code

    Returns: list of (contract name, type)
    """
    # remove comments in case they contain code snippets that could fail the regex
    comment_regex = r"(?:\s*\/\/[^\n]*)|(?:\/\*[\s\S]*?\*\/)"
    uncommented_source = regex_sub(comment_regex, "", full_source)
    contracts = regex_findall(
        r"((?:abstract contract|contract|library|interface)\s[^;{]*{[\s\S]*?})\s*(?=(?:abstract contract|contract|library|interface|pragma|struct|enum)\s|$)",  # NOQA: E501
        uncommented_source,
    )

    contract_names = []
    for source in contracts:
        if matches := regex_findall(
            r"(abstract contract|contract|library|interface)\s+(\S*)\s*(?:is\s+([\s\S]*?)|)(?:{)",
            source,
        ):
            type_, name, _ = matches[0]
            contract_names.append((name, type_))
    return contract_names


def _strip_solidity_comments_and_strings(source: str) -> str:
    chars: list[str] = []
    idx = 0
    state = "normal"
    quote = ""

    while idx < len(source):
        char = source[idx]
        next_char = source[idx + 1] if idx + 1 < len(source) else ""

        if state == "normal":
            if char == "/" and next_char == "/":
                state = "line_comment"
                chars.extend("  ")
                idx += 2
                continue
            if char == "/" and next_char == "*":
                state = "block_comment"
                chars.extend("  ")
                idx += 2
                continue
            if char in {"'", '"'}:
                state = "string"
                quote = char
                chars.append(" ")
                idx += 1
                continue
            chars.append(char)
            idx += 1
            continue

        if state == "line_comment":
            chars.append("\n" if char == "\n" else " ")
            if char == "\n":
                state = "normal"
            idx += 1
            continue

        if state == "block_comment":
            if char == "*" and next_char == "/":
                chars.extend("  ")
                state = "normal"
                idx += 2
            else:
                chars.append("\n" if char == "\n" else " ")
                idx += 1
            continue

        if state == "string":
            if char == "\\":
                chars.extend("  ")
                idx += 2
                continue
            chars.append("\n" if char == "\n" else " ")
            if char == quote:
                state = "normal"
            idx += 1

    return "".join(chars)


def get_pragma_spec(source: str, path: str | None = None) -> SolidityPragmaSpec:
    """
    Extracts pragma information from Solidity source code.

    Args:
        source: Solidity source code
        path: Optional path to the source (only used for error reporting)

    Returns: SolidityPragmaSpec object
    """

    clean_source = _strip_solidity_comments_and_strings(source)
    pragma_strings = [
        " ".join(match.groups()[0].split())
        for match in regex_finditer(r"\bpragma +solidity([^;]*);", clean_source)
    ]
    if pragma_strings:
        try:
            return SolidityPragmaSpec(pragma_strings)
        except ValueError as exc:
            path = "" if path is None else f"{path}: "
            raise PragmaError(f"{path}{exc}") from exc
    if path:
        raise PragmaError(f"No version pragma in '{path}'")
    raise PragmaError("String does not contain a version pragma")


def get_vyper_pragma_spec(source: str, path: str | None = None) -> VyperPragmaSpec:
    """
    Extracts pragma information from Vyper source code.

    Args:
        source: Vyper source code
        path: Optional path to the source (only used for error reporting)

    Returns: VyperPragmaSpec object
    """
    pragma_matches: list[tuple[str, str]] = []
    try:
        token_list = tokenize(io.BytesIO(source.encode("utf-8")).readline)
        for token in token_list:
            if token.type != COMMENT:
                continue

            contents = token.string[1:].strip()
            if contents.startswith("@version"):
                pragma_matches.append(("@version", contents.removeprefix("@version").strip()))
            elif contents.startswith("pragma "):
                pragma = contents.removeprefix("pragma ").strip()
                if pragma.startswith("version "):
                    pragma_matches.append(
                        ("pragma version", pragma.removeprefix("version ").strip())
                    )
    except TokenError as exc:
        path = "" if path is None else f"{path}: "
        raise PragmaError(f"{path}Cannot parse Vyper source: {exc.args[0]}") from exc

    if not pragma_matches:
        if path:
            raise PragmaError(f"No version pragma in '{path}'")
        raise PragmaError("String does not contain a version pragma")
    if len(pragma_matches) > 1:
        path = "" if path is None else f"{path}: "
        raise PragmaError(f"{path}Vyper version pragma specified multiple times")

    directive, pragma_string = pragma_matches[0]
    pragma_string = " ".join(pragma_string.split())
    try:
        return VyperPragmaSpec(pragma_string, allow_legacy=directive == "@version")
    except ValueError:
        path = "" if path is None else f"{path}: "
        raise PragmaError(f"{path}Cannot parse Vyper version from pragma: {pragma_string}")
