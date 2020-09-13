#!/usr/bin/python3

from typing import Dict, ItemsView, List, Optional, Tuple, Union

from .sources import Sources, highlight_source

INTERFACE_KEYS = ["abi", "contractName", "sha1", "type"]

DEPLOYMENT_KEYS = [
    "abi",
    "ast",
    "bytecode",
    "compiler",
    "contractName",
    "deployedBytecode",
    "deployedSourceMap",
    "language",
    "natspec",
    "opcodes",
    "pcMap",
    "sourceMap",
    "type",
]

BUILD_KEYS = [
    "allSourcePaths",
    "bytecodeSha1",
    "coverageMap",
    "dependencies",
    "offset",
    "sha1",
    "source",
    "sourcePath",
] + DEPLOYMENT_KEYS

_revert_map: Dict = {}


class Build:

    """Methods for accessing and manipulating a project's contract build data."""

    def __init__(self, sources: Sources) -> None:
        self._sources = sources
        self._contracts: Dict = {}
        self._interfaces: Dict = {}

    def _add_contract(self, build_json: Dict) -> None:
        contract_name = build_json["contractName"]
        if contract_name in self._contracts and build_json["type"] == "interface":
            return
        self._contracts[contract_name] = build_json
        if "pcMap" not in build_json:
            # no pcMap means build artifact is for an interface
            return
        if "0" in build_json["pcMap"]:
            build_json["pcMap"] = dict((int(k), v) for k, v in build_json["pcMap"].items())
        self._generate_revert_map(
            build_json["pcMap"], build_json["allSourcePaths"], build_json["language"]
        )

    def _add_interface(self, build_json: Dict) -> None:
        contract_name = build_json["contractName"]
        self._interfaces[contract_name] = build_json

    def _generate_revert_map(self, pcMap: Dict, source_map: Dict, language: str) -> None:
        # Adds a contract's dev revert strings to the revert map and it's pcMap
        marker = "//" if language == "Solidity" else "#"
        for pc, data in (
            (k, v)
            for k, v in pcMap.items()
            if v["op"] in ("REVERT", "INVALID") or "jump_revert" in v
        ):
            if "path" not in data:
                continue
            path_str = source_map[data["path"]]

            if "dev" not in data:
                if "fn" not in data or "first_revert" in data:
                    _revert_map[pc] = False
                    continue
                try:
                    revert_str = self._sources.get(path_str)[data["offset"][1] :]
                    revert_str = revert_str[: revert_str.index("\n")]
                    revert_str = revert_str[revert_str.index(marker) + len(marker) :].strip()
                    if revert_str.startswith("dev:"):
                        data["dev"] = revert_str
                except (KeyError, ValueError):
                    pass

            msg = "" if data["op"] == "REVERT" else "invalid opcode"
            revert = (
                path_str,
                tuple(data["offset"]),
                data.get("fn", "<None>"),
                data.get("dev", msg),
                self._sources,
            )

            # do not compare the final tuple item in case the same project was loaded twice
            if pc not in _revert_map or (_revert_map[pc] and revert[:-1] == _revert_map[pc][:-1]):
                _revert_map[pc] = revert
                continue
            _revert_map[pc] = False

    def _remove_contract(self, contract_name: str) -> None:
        key = self._stem(contract_name)
        if key in self._contracts:
            del self._contracts[key]

    def _remove_interface(self, contract_name: str) -> None:
        key = self._stem(contract_name)
        if key in self._interfaces:
            del self._interfaces[key]

    def get(self, contract_name: str) -> Dict:
        """Returns build data for the given contract name."""
        return self._contracts[self._stem(contract_name)]

    def items(self, path: Optional[str] = None) -> Union[ItemsView, List]:
        """Provides an list of tuples as (key,value), similar to calling dict.items.
        If a path is given, only contracts derived from that source file are returned."""
        items = list(self._contracts.items()) + list(self._interfaces.items())
        if path is None:
            return items
        return [(k, v) for k, v in items if v.get("sourcePath") == path]

    def contains(self, contract_name: str) -> bool:
        """Checks if the contract name exists in the currently loaded build data."""
        return self._stem(contract_name) in list(self._contracts) + list(self._interfaces)

    def get_dependents(self, contract_name: str) -> List:
        """Returns a list of contract names that inherit from or link to the given
        contract. Used by the compiler when determining which contracts to recompile
        based on a changed source file."""
        return [k for k, v in self._contracts.items() if contract_name in v.get("dependencies", [])]

    def _stem(self, contract_name: str) -> str:
        return contract_name.replace(".json", "")


def _get_dev_revert(pc: int) -> Optional[str]:
    # Given the program counter from a stack trace that caused a transaction
    # to revert, returns the commented dev string (if any)
    if pc not in _revert_map or _revert_map[pc] is False:
        return None
    return _revert_map[pc][3]


def _get_error_source_from_pc(pc: int, pad: int = 3) -> Tuple:
    # Given the program counter from a stack trace that caused a transaction
    # to revert, returns the highlighted relevent source code and the method name.
    if pc not in _revert_map or _revert_map[pc] is False:
        return (None,) * 4
    revert = _revert_map[pc]
    source = revert[4].get(revert[0])
    highlight, linenos = highlight_source(source, revert[1], pad=pad)  # type: ignore
    return highlight, linenos, revert[0], revert[2]
