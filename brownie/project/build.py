#!/usr/bin/python3
# mypy: disable-error-code="index"

from typing import (
    Any,
    Dict,
    Final,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    final,
)

from brownie.typing import (
    BuildJson,
    ContractBuildJson,
    ContractName,
    InterfaceBuildJson,
    Language,
    Offset,
    ProgramCounter,
)

from .sources import Sources, highlight_source

INTERFACE_KEYS: Final = "abi", "contractName", "sha1", "type"

DEPLOYMENT_KEYS: Final = (
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
)

BUILD_KEYS: Final = (
    "allSourcePaths",
    "bytecodeSha1",
    "coverageMap",
    "dependencies",
    "offset",
    "sha1",
    "source",
    "sourcePath",
) + DEPLOYMENT_KEYS

_revert_map: Final[Dict[int | str, tuple | Literal[False]]] = {}


class BytecodeJSON(TypedDict, total=False):
    object: HexStr

class BuildJSON(TypedDict, total=False):
    type: Literal["contract", "interface"]
    contractName: ContractName
    language: Language
    sourcePath: str
    pcMap: Dict[str | int, Any]
    allSourcePaths: Dict[str, Any]
    offset: tuple
    bytecode: BytecodeJSON
    bytecodeSha1: HexStr
    
@final
class Build:
    """Methods for accessing and manipulating a project's contract build data."""

    def __init__(self, sources: Sources) -> None:
        self._sources: Final = sources
        self._contracts: Final[Dict[ContractName, ContractBuildJson]] = {}
        self._interfaces: Final[Dict[ContractName, InterfaceBuildJson]] = {}

    def _add_contract(
        self,
        build_json: ContractBuildJson,
        alias: Optional[ContractName] = None,
    ) -> None:
        contract_name = alias or build_json["contractName"]
        if contract_name in self._contracts and build_json["type"] == "interface":
            return
        if build_json["sourcePath"].startswith("interface"):
            # interfaces should generate artifact in /build/interfaces/ not /build/contracts/
            return
        self._contracts[contract_name] = build_json
        if "pcMap" not in build_json:
            # no pcMap means build artifact is for an interface
            return

        pc_map: Dict[int | str, ProgramCounter] = build_json["pcMap"]  # type: ignore [assignment]
        if "0" in pc_map:
            build_json["pcMap"] = {int(k): pc_map[k] for k in pc_map}
        self._generate_revert_map(pc_map, build_json["allSourcePaths"], build_json["language"])

    def _add_interface(self, build_json: InterfaceBuildJson) -> None:
        contract_name = build_json["contractName"]
        self._interfaces[contract_name] = build_json

    def _generate_revert_map(
        self,
        pcMap: Dict[int | str, ProgramCounter],
        source_map: Dict[str, str],
        language: Language,
    ) -> None:
        # Adds a contract's dev revert strings to the revert map and it's pcMap
        marker = "//" if language == "Solidity" else "#"
        for pc, data in pcMap.items():
            if data["op"] in ("REVERT", "INVALID") or "jump_revert" in data:
                if "path" not in data or data["path"] is None:
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

    def _remove_contract(self, contract_name: ContractName) -> None:
        key = self._stem(contract_name)
        if key in self._contracts:
            del self._contracts[key]

    def _remove_interface(self, contract_name: ContractName) -> None:
        key = self._stem(contract_name)
        if key in self._interfaces:
            del self._interfaces[key]

    def get(self, contract_name: ContractName) -> BuildJson:
        """Returns build data for the given contract name."""
        key = self._stem(contract_name)
        if key in self._contracts:
            return self._contracts[key]
        return self._interfaces[key]

    def items(
        self,
        path: Optional[str] = None,
    ) -> List[Tuple[ContractName, BuildJson]]:
        """Provides an list of tuples as (key,value), similar to calling dict.items.
        If a path is given, only contracts derived from that source file are returned."""
        items = [*self._contracts.items(), *self._interfaces.items()]
        if path is None:
            return items
        return [(k, v) for k, v in items if v.get("sourcePath") == path]

    def contains(self, contract_name: ContractName) -> bool:
        """Checks if the contract name exists in the currently loaded build data."""
        stem = self._stem(contract_name)
        return stem in self._contracts or stem in self._interfaces

    def get_dependents(self, contract_name: ContractName) -> List[ContractName]:
        """Returns a list of contract names that inherit from or link to the given
        contract. Used by the compiler when determining which contracts to recompile
        based on a changed source file."""
        return [k for k, v in self._contracts.items() if contract_name in v.get("dependencies", [])]

    def _stem(self, contract_name: ContractName) -> ContractName:
        return contract_name.replace(".json", "")  # type: ignore [return-value]


def _get_dev_revert(pc: int) -> Optional[str]:
    # Given the program counter from a stack trace that caused a transaction
    # to revert, returns the commented dev string (if any)
    if pc not in _revert_map:
        return None
    revert = _revert_map[pc]
    if revert is False:
        return None
    return revert[3]


def _get_error_source_from_pc(
    pc: int, pad: int = 3
) -> Tuple[Optional[str], Optional[Tuple[int, int]], Optional[str], Optional[str]]:
    # Given the program counter from a stack trace that caused a transaction
    # to revert, returns the highlighted relevent source code and the method name.
    if pc not in _revert_map or _revert_map[pc] is False:
        return (None,) * 4
    revert: Tuple[str, Offset, str, str, Sources] = _revert_map[pc]  # type: ignore [assignment]
    source = revert[4].get(revert[0])  # type: ignore [index]
    highlight, linenos = highlight_source(source, revert[1], pad=pad)
    return highlight, linenos, revert[0], revert[2]  # type: ignore [index]
