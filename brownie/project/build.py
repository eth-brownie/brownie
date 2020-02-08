#!/usr/bin/python3

from typing import Dict, ItemsView, List, Optional, Sequence, Tuple, Union

from .sources import Sources, highlight_source

BUILD_KEYS = [
    "abi",
    "allSourcePaths",
    "ast",
    "bytecode",
    "bytecodeSha1",
    "compiler",
    "contractName",
    "coverageMap",
    "deployedBytecode",
    "deployedSourceMap",
    "dependencies",
    "language",
    "offset",
    "opcodes",
    "pcMap",
    "sha1",
    "source",
    "sourceMap",
    "sourcePath",
    "type",
]

_revert_map: Dict = {}


class Build:

    """Methods for accessing and manipulating a project's contract build data."""

    def __init__(self, sources: Sources) -> None:
        self._sources = sources
        self._build: Dict = {}

    def _add(self, build_json: Dict) -> None:
        contract_name = build_json["contractName"]
        if "0" in build_json["pcMap"]:
            build_json["pcMap"] = dict((int(k), v) for k, v in build_json["pcMap"].items())
        if build_json["compiler"]["minify_source"]:
            build_json = self.expand_build_offsets(build_json)
        self._build[contract_name] = build_json
        self._generate_revert_map(build_json["pcMap"], build_json["language"])

    def _generate_revert_map(self, pcMap: Dict, language: str) -> None:
        # Adds a contract's dev revert strings to the revert map and it's pcMap
        marker = "//" if language == "Solidity" else "#"
        for pc, data in (
            (k, v)
            for k, v in pcMap.items()
            if v["op"] in ("REVERT", "INVALID") or "jump_revert" in v
        ):
            if "dev" not in data:
                if "fn" not in data or "first_revert" in data:
                    _revert_map[pc] = False
                    continue
                try:
                    revert_str = self._sources.get(data["path"])[data["offset"][1] :]
                    revert_str = revert_str[: revert_str.index("\n")]
                    revert_str = revert_str[revert_str.index(marker) + len(marker) :].strip()
                    if revert_str.startswith("dev:"):
                        data["dev"] = revert_str
                except (KeyError, ValueError):
                    pass

            msg = "" if data["op"] == "REVERT" else "invalid opcode"
            revert = (
                data["path"],
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

    def _remove(self, contract_name: str) -> None:
        del self._build[self._stem(contract_name)]

    def get(self, contract_name: str) -> Dict:
        """Returns build data for the given contract name."""
        return self._build[self._stem(contract_name)]

    def items(self, path: Optional[str] = None) -> Union[ItemsView, List]:
        """Provides an list of tuples as (key,value), similar to calling dict.items.
        If a path is given, only contracts derived from that source file are returned."""
        if path is None:
            return self._build.items()
        return [(k, v) for k, v in self._build.items() if v["sourcePath"] == path]

    def contains(self, contract_name: str) -> bool:
        """Checks if the contract name exists in the currently loaded build data."""
        return self._stem(contract_name) in self._build

    def get_dependents(self, contract_name: str) -> List:
        """Returns a list of contract names that inherit from or link to the given
        contract. Used by the compiler when determining which contracts to recompile
        based on a changed source file."""
        return [k for k, v in self._build.items() if contract_name in v["dependencies"]]

    def _stem(self, contract_name: str) -> str:
        return contract_name.replace(".json", "")

    def expand_build_offsets(self, build_json: Dict) -> Dict:
        """Expands minified source offsets in a build json dict."""

        offset_map: Dict = {}
        name = build_json["contractName"]

        # minification only happens to the target contract that was compiled,
        # so we ignore any import sources
        source_path = build_json["sourcePath"]

        for value in (
            v
            for v in build_json["pcMap"].values()
            if "offset" in v and "path" in v and v["path"] == source_path
        ):
            value["offset"] = self._get_offset(offset_map, name, value["offset"])

        for key in ("branches", "statements"):
            if source_path not in build_json["coverageMap"][key]:
                continue
            coverage_map = build_json["coverageMap"][key][source_path]
            for fn, value in coverage_map.items():
                coverage_map[fn] = dict(
                    (k, self._get_offset(offset_map, name, v[:2]) + tuple(v[2:]))
                    for k, v in value.items()
                )
        return build_json

    def _get_offset(self, offset_map: Dict, name: str, offset: Sequence[int]) -> Tuple:
        offset = tuple(offset)
        if offset not in offset_map:
            offset_map[offset] = self._sources.expand_offset(name, offset)
        return offset_map[offset]


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
