#!/usr/bin/python3

import logging
from typing import Any, Deque, Dict, Final, List, Optional, Set, Tuple

import semantic_version
import solcast
import solcx
from eth_typing import ABIElement, HexStr
from requests.exceptions import ConnectionError
from solcast.nodes import NodeBase, is_inside_offset

from brownie._c_constants import Version, deque, sha1
from brownie._config import EVM_EQUIVALENTS
from brownie.exceptions import SOLIDITY_ERROR_CODES, CompilerError, IncompatibleSolcVersion  # noqa
from brownie.project.compiler.utils import (
    VersionList,
    VersionSpec,
    _get_alias,
    expand_source_map,
)
from brownie.typing import (
    BytecodeJson,
    DeployedBytecodeJson,
    InputJsonSolc,
    Offset,
    SolidityBuildJson,
    Source,
)

from . import sources

solcx_logger: Final = logging.getLogger("solcx")
solcx_logger.setLevel(10)
sh: Final = logging.StreamHandler()
sh.setLevel(10)
sh.setFormatter(logging.Formatter("%(message)s"))
solcx_logger.addHandler(sh)

AVAILABLE_SOLC_VERSIONS: Optional[VersionList] = None

EVM_VERSION_MAPPING: Final = [
    ("prague", Version("0.8.30")),
    ("cancun", Version("0.8.25")),
    ("shanghai", Version("0.8.20")),
    ("paris", Version("0.8.18")),
    ("london", Version("0.8.7")),
    ("berlin", Version("0.8.5")),
    ("istanbul", Version("0.5.13")),
    ("petersburg", Version("0.5.5")),
    ("byzantium", Version("0.4.0")),
]

PcMap = Dict[int, Dict[str, Any]]
StatementNodes = Dict[str, Set[Offset]]
StatementMap = Dict[str, Dict[str, Dict[int, Tuple[int, int]]]]
BranchNodes = Dict[str, Set[NodeBase]]
BranchMap = Dict[str, Dict[str, Dict[int, Tuple[int, int, int]]]]

_BINOPS_PARAMS: Final = {"nodeType": "BinaryOperation", "typeDescriptions.typeString": "bool"}


def get_version() -> semantic_version.Version:
    return solcx.get_solc_version(with_commit_hash=True)


def compile_from_input_json(
    input_json: InputJsonSolc, silent: bool = True, allow_paths: Optional[str] = None
) -> Dict:
    """
    Compiles contracts from a standard input json.

    Args:
        input_json: solc input json
        silent: verbose reporting
        allow_paths: compiler allowed filesystem import path

    Returns: standard compiler output json
    """

    settings = input_json["settings"]
    settings.setdefault("evmVersion", None)
    if settings["evmVersion"] in EVM_EQUIVALENTS:
        settings["evmVersion"] = EVM_EQUIVALENTS[settings["evmVersion"]]

    if not silent:
        print(f"Compiling contracts...\n  Solc version: {str(solcx.get_solc_version())}")

        optimizer = settings["optimizer"]
        opt = f"Enabled  Runs: {optimizer['runs']}" if optimizer["enabled"] else "Disabled"
        print(f"  Optimizer: {opt}")

        if settings["evmVersion"]:
            print(f"  EVM Version: {settings['evmVersion'].capitalize()}")

    try:
        return solcx.compile_standard(input_json, allow_paths=allow_paths)
    except solcx.exceptions.SolcError as e:
        raise CompilerError(e, "solc")


def set_solc_version(version: VersionSpec) -> str:
    """Sets the solc version. If not available it will be installed."""
    if not isinstance(version, Version):
        version = Version(version.lstrip("v"))
    if version < Version("0.4.22"):
        raise IncompatibleSolcVersion("Brownie only supports Solidity versions >=0.4.22")
    try:
        solcx.set_solc_version(version, silent=True)
    except solcx.exceptions.SolcNotInstalled:
        if version not in _get_solc_version_list()[0]:
            raise IncompatibleSolcVersion(
                f"Cannot install Solidity v{version} on this OS. You may be able to "
                f"manually compile from source with `solcx.compile_solc('{version}')`"
            )
        install_solc(version)
        solcx.set_solc_version(version, silent=True)
    return str(solcx.get_solc_version())


def install_solc(*versions: VersionSpec) -> None:
    """Installs solc versions."""
    for version in versions:
        solcx.install_solc(version, show_progress=False)


def get_abi(contract_source: str, allow_paths: Optional[str] = None) -> Dict[str, List[ABIElement]]:
    """
    Given a contract source, returns a dict of {name: abi}

    This function is deprecated in favor of `brownie.project.compiler.get_abi`
    """
    version = find_best_solc_version({"<stdin>": contract_source})
    set_solc_version(version)
    compiled: Dict[str, dict] = solcx.compile_source(
        contract_source, allow_empty=True, allow_paths=allow_paths, output_values=["abi"]
    )
    return {k.rsplit(":")[-1]: v["abi"] for k, v in compiled.items()}


def find_solc_versions(
    contract_sources: Dict[str, str],
    install_needed: bool = False,
    install_latest: bool = False,
    silent: bool = True,
) -> Dict[str, List[str]]:
    """
    Analyzes contract pragmas and determines which solc version(s) to use.

    Args:
        contract_sources: a dictionary in the form of {'path': "source code"}
        install_needed: if True, will install when no installed version matches
                        the contract pragma
        install_latest: if True, will install when a newer version is available
                        than the installed one
        silent: set to False to enable verbose reporting

    Returns: dictionary of {'version': ['path', 'path', ..]}
    """

    available_versions, installed_versions = _get_solc_version_list()

    pragma_specs: Dict = {}
    to_install = set()
    new_versions = set()

    for path, source in contract_sources.items():
        pragma_spec = sources.get_pragma_spec(source, path)
        pragma_specs[path] = pragma_spec
        version = pragma_spec.select(installed_versions)

        if not version and not install_needed and not install_latest:
            raise IncompatibleSolcVersion(
                f"No installed solc version matching '{pragma_spec}' in '{path}'"
            )

        # if no installed version of solc matches the pragma, find the latest available version
        latest = pragma_spec.select(available_versions)

        if not version and not latest:
            raise IncompatibleSolcVersion(
                f"No installable solc version matching '{pragma_spec}' in '{path}'"
            )

        if not version or (install_latest and latest > version):
            to_install.add(latest)
        elif latest and latest > version:
            new_versions.add(str(version))

    # install new versions if needed
    if to_install:
        install_solc(*to_install)
        installed_versions = solcx.get_installed_solc_versions()
    elif new_versions and not silent:
        print(
            f"New compatible solc version{'s' if len(new_versions) > 1 else ''}"
            f" available: {', '.join(new_versions)}"
        )

    # organize source paths by latest available solc version
    compiler_versions: Dict[str, List[str]] = {}
    for path, spec in pragma_specs.items():
        version = spec.select(installed_versions)
        compiler_versions.setdefault(str(version), []).append(path)

    return compiler_versions


def find_best_solc_version(
    contract_sources: Dict[str, str],
    install_needed: bool = False,
    install_latest: bool = False,
    silent: bool = True,
) -> str:
    """
    Analyzes contract pragmas and finds the best version compatible with all sources.

    Args:
        contract_sources: a dictionary in the form of {'path': "source code"}
        install_needed: if True, will install when no installed version matches
                        the contract pragma
        install_latest: if True, will install when a newer version is available
                        than the installed one
        silent: set to False to enable verbose reporting

    Returns: version string
    """
    available_versions: VersionList
    installed_versions: VersionList

    available_versions, installed_versions = _get_solc_version_list()

    for path, source in contract_sources.items():
        pragma_spec = sources.get_pragma_spec(source, path)
        installed_versions = [i for i in installed_versions if i in pragma_spec]
        available_versions = [i for i in available_versions if i in pragma_spec]

    if not available_versions:
        raise IncompatibleSolcVersion("No installable solc version compatible across all sources")

    if not installed_versions and not install_needed and not install_latest:
        raise IncompatibleSolcVersion("No installed solc version compatible across all sources")

    if max(available_versions) > max(installed_versions, default=Version("0.0.0")):
        if install_latest or (install_needed and not installed_versions):
            install_solc(max(available_versions))
            return str(max(available_versions))
        if not silent:
            print(f"New compatible solc version available: {max(available_versions)}")

    return str(max(installed_versions))


def _get_solc_version_list() -> Tuple[VersionList, VersionList]:
    global AVAILABLE_SOLC_VERSIONS
    installed_versions: VersionList = solcx.get_installed_solc_versions()
    if AVAILABLE_SOLC_VERSIONS is None:
        try:
            AVAILABLE_SOLC_VERSIONS = solcx.get_installable_solc_versions()
        except ConnectionError:
            if not installed_versions:
                raise ConnectionError("Solc not installed and cannot connect to GitHub")
            AVAILABLE_SOLC_VERSIONS = installed_versions
    return AVAILABLE_SOLC_VERSIONS, installed_versions


def _get_unique_build_json(
    output_evm: Dict,
    contract_node: Any,
    stmt_nodes: StatementNodes,
    branch_nodes: BranchNodes,
    has_fallback: bool,
) -> SolidityBuildJson:
    paths = {
        str(i.contract_id): i.parent().absolutePath
        for i in [contract_node] + contract_node.dependencies
    }

    bytecode = _format_link_references(output_evm)
    bytecode_json: DeployedBytecodeJson = output_evm["deployedBytecode"]

    without_metadata = _remove_metadata(bytecode_json["object"])
    instruction_count = len(without_metadata) // 2

    pc_map, statement_map, branch_map = _generate_coverage_data(
        bytecode_json["sourceMap"],
        bytecode_json["opcodes"],
        contract_node,
        stmt_nodes,
        branch_nodes,
        has_fallback,
        instruction_count,
    )

    dependencies = []
    for node in contract_node.dependencies:
        if node.nodeType == "ContractDefinition":
            # use contract aliases when recording dependencies, to avoid
            # potential namespace collisions when importing across projects
            name = node.name
            path_str = node.parent().absolutePath
            dependencies.append(_get_alias(name, path_str))

    # This is not a complete SolidityBuildJson object but that's okay for now
    # TODO: make a partial SolidityBuildJson subclass for this dtype
    build_json: SolidityBuildJson = {  # type: ignore [typeddict-item]
        "allSourcePaths": paths,
        "bytecode": bytecode,
        "bytecodeSha1": sha1(_remove_metadata(bytecode).encode()).hexdigest(),  # type: ignore [typeddict-item]
        "coverageMap": {"statements": statement_map, "branches": branch_map},
        "dependencies": dependencies,
        "offset": contract_node.offset,
        "pcMap": pc_map,
        "type": contract_node.contractKind,
    }
    return build_json


def _format_link_references(evm: Dict) -> HexStr:
    # Standardizes formatting for unlinked libraries within bytecode
    bytecode_json: BytecodeJson = evm["bytecode"]
    bytecode = bytecode_json["object"]
    link_refs: Dict[str, dict] = bytecode_json.get("linkReferences", {})
    references = ((k, x) for v in link_refs.values() for k, x in v.items())
    for n, loc in ((i[0], x["start"] * 2) for i in references for x in i[1]):
        bytecode = f"{bytecode[:loc]}__{n[:36]:_<36}__{bytecode[loc+40:]}"  # type: ignore [assignment]
    return bytecode


def _remove_metadata(bytecode: HexStr) -> HexStr:
    return bytecode[: -(int(bytecode[-4:], 16) + 2) * 2] if bytecode else ""  # type: ignore [return-value]


def _generate_coverage_data(
    source_map_str: str,
    opcodes_str: str,
    contract_node: Any,
    stmt_nodes: StatementNodes,
    branch_nodes: BranchNodes,
    has_fallback: bool,
    instruction_count: int,
) -> Tuple[PcMap, StatementMap, BranchMap]:
    # Generates data used by Brownie for debugging and coverage evaluation
    if not opcodes_str:
        return {}, {}, {}

    source_map = deque(expand_source_map(source_map_str))
    opcodes = deque(opcodes_str.split(" "))

    contract_nodes = [contract_node] + contract_node.dependencies
    source_nodes = {str(i.contract_id): i.parent() for i in contract_nodes}

    stmt_nodes = {i: stmt_nodes[i].copy() for i in source_nodes}
    statement_map: StatementMap = {i: {} for i in source_nodes}

    # possible branch offsets
    branch_original = {i: branch_nodes[i].copy() for i in source_nodes}
    branch_nodes = {i: {i.offset for i in branch_nodes[i]} for i in source_nodes}
    # currently active branches, awaiting a jumpi
    branch_active: Dict[str, Dict[Offset, int]] = {i: {} for i in source_nodes}
    # branches that have been set
    branch_set: Dict[str, Dict[Offset, Tuple[int, int]]] = {i: {} for i in source_nodes}

    count, pc = 0, 0
    pc_list: List[dict] = []
    revert_map: Dict[Tuple[str, int], List[int]] = {}
    fallback_hexstr: str = "unassigned"

    optimizer_revert = get_version() < Version("0.8.0")

    active_source_node: Optional[NodeBase] = None
    active_fn_node: Optional[NodeBase] = None
    active_fn_name: Optional[str] = None
    first_source = source_map[0]

    while source_map and source_map[-1][2] == -1:
        # trim the end of the source map where there are no contracts associated
        # this is required because sometimes the source map is too long
        # likely a side effect of the YUL optimizer ¯\_(ツ)_/¯
        source_map.pop()

    while source_map:
        # format of source_map is [start, stop, contract_id, jump code]
        source = source_map.popleft()
        pc_list.append({"op": opcodes.popleft(), "pc": pc})

        if (
            has_fallback is False
            and fallback_hexstr == "unassigned"
            and pc_list[-1]["op"] == "REVERT"
            and [i["op"] for i in pc_list[-4:-1]] == ["JUMPDEST", "PUSH1", "DUP1"]
        ):
            # flag the REVERT op at the end of the function selector,
            # later reverts may jump to it instead of having their own REVERT op
            fallback_hexstr = f"0x{hex(pc - 4).upper()[2:]}"
            pc_list[-1]["first_revert"] = True

        if source[3] != "-":
            pc_list[-1]["jump"] = source[3]

        pc += 1
        if pc_list[-1]["op"].startswith("PUSH") and opcodes[0][:2] == "0x":
            pc_list[-1]["value"] = opcodes.popleft()
            pc += int(pc_list[-1]["op"][4:])

        # for REVERT opcodes without an source offset, try to infer one
        if (source[2] == -1 or source == first_source) and pc_list[-1]["op"] == "REVERT":
            _find_revert_offset(
                pc_list, source_map, active_source_node, active_fn_node, active_fn_name
            )
        if source[2] == -1:
            continue

        # set contract path (-1 means none)
        contract_id = str(source[2])
        if contract_id not in source_nodes:
            # In Solidity >=0.7.2 contract ID can reference an AST within the YUL-optimization
            # "generatedSources". Brownie does not support coverage evaluation within these
            # sources, so we consider to this to be unmapped.
            continue

        active_source_node = source_nodes[contract_id]
        pc_list[-1]["path"] = contract_id

        # set source offset (-1 means none)
        if source[0] == -1:
            continue
        offset: Offset = (source[0], source[0] + source[1])  # type: ignore [assignment]
        pc_list[-1]["offset"] = offset

        if pc_list[-1]["op"] == "REVERT" and not optimizer_revert:
            # In Solidity >=0.8.0, an optimization is applied to reverts with an error string
            # such that all reverts appear to happen at the same point in the source code.
            # We mark this REVERT as the "optimizer revert" so that when it's encountered in
            # a trace we know to look back to find the actual revert location.
            if fn_node := active_source_node.children(
                include_parents=False,
                include_children=True,
                required_offset=offset,
                filters=(
                    {"nodeType": "FunctionCall", "expression.name": "revert"},
                    {"nodeType": "FunctionCall", "expression.name": "require"},
                ),
            ):
                args = len(fn_node[0].arguments)
                if args == 2 or (fn_node[0].expression.name == "revert" and args):
                    optimizer_revert = True
                    pc_list[-1]["optimizer_revert"] = True

        # add error messages for INVALID opcodes
        if pc_list[-1]["op"] == "INVALID":
            _set_invalid_error_string(active_source_node, pc_list[-1])

        # for JUMPI instructions, set active branch markers
        if branch_active[contract_id] and pc_list[-1]["op"] == "JUMPI":
            for offset in branch_active[contract_id]:
                # ( program counter index, JUMPI index)
                branch_set[contract_id][offset] = (
                    branch_active[contract_id][offset],
                    len(pc_list) - 1,
                )
            branch_active[contract_id].clear()

        # if op relates to previously set branch marker, clear it
        elif offset in branch_nodes[contract_id]:
            if offset in branch_set[contract_id]:
                del branch_set[contract_id][offset]
            branch_active[contract_id][offset] = len(pc_list) - 1

        try:
            # set fn name and statement coverage marker
            if "offset" in pc_list[-2] and offset == pc_list[-2]["offset"]:
                pc_list[-1]["fn"] = active_fn_name
            else:
                active_fn_node, active_fn_name = _get_active_fn(active_source_node, offset)
                pc_list[-1]["fn"] = active_fn_name
                stmt_offset: Offset = next(
                    i for i in stmt_nodes[contract_id] if sources.is_inside_offset(offset, i)
                )
                stmt_nodes[contract_id].discard(stmt_offset)
                statement_map[contract_id].setdefault(active_fn_name, {})[count] = stmt_offset
                pc_list[-1]["statement"] = count
                count += 1
        except (KeyError, IndexError, StopIteration):
            pass

        if pc_list[-1].get("value", None) == fallback_hexstr and opcodes[0] in ("JUMP", "JUMPI"):
            # track all jumps to the initial revert
            key = (pc_list[-1]["path"], pc_list[-1]["offset"])
            revert_map.setdefault(key, []).append(len(pc_list))

    while opcodes[0] not in ("INVALID", "STOP") and pc < instruction_count:
        # necessary because sometimes solidity returns an incomplete source map
        pc_list.append({"op": opcodes.popleft(), "pc": pc})
        pc += 1
        if pc_list[-1]["op"].startswith("PUSH") and opcodes[0][:2] == "0x":
            pc_list[-1]["value"] = opcodes.popleft()
            pc += int(pc_list[-1]["op"][4:])

    # compare revert and require statements against the map of revert jumps
    for (contract_id, fn_offset), values in revert_map.items():
        fn_node = source_nodes[contract_id].children(
            depth=2,
            include_children=False,
            required_offset=fn_offset,
            filters={"nodeType": "FunctionDefinition"},
        )
        if len(fn_node) == 0:
            # In Solidity >=0.8.13, with the viaIR option set, there is a dispatch
            # function present in the generated bytecode
            continue
        revert_nodes = fn_node[0].children(
            filters=(
                {"nodeType": "FunctionCall", "expression.name": "revert"},
                {"nodeType": "FunctionCall", "expression.name": "require"},
            )
        )
        for node in revert_nodes:
            offset = node.offset
            # if the node offset is not in the source map, apply it's offset to the JUMPI op
            if not any("offset" in x and x["offset"] == offset for x in pc_list):
                pc_list[values[0]].update(offset=offset, jump_revert=True)
                del values[0]

    # set branch index markers and build final branch map
    branch_map: BranchMap = {i: {} for i in source_nodes}
    for path, markers in branch_set.items():
        for offset, idx in markers.items():
            # for branch to be hit, need an op relating to the source and the next JUMPI
            # this is because of how the compiler optimizes nested BinaryOperations
            if "fn" in pc_list[idx[0]]:
                fn = pc_list[idx[0]]["fn"]
                pc_list[idx[0]]["branch"] = count
                pc_list[idx[1]]["branch"] = count
                node = next(i for i in branch_original[path] if i.offset == offset)
                branch_map[path].setdefault(fn, {})[count] = offset + (node.jump,)
                count += 1

    pc_map: PcMap = {i.pop("pc"): i for i in pc_list}
    return pc_map, statement_map, branch_map


def _find_revert_offset(
    pc_list: List[dict],
    source_map: Deque[Source],
    source_node: NodeBase,
    fn_node: NodeBase,
    fn_name: Optional[str],
) -> None:
    # attempt to infer a source offset for reverts that do not have one

    if source_map:
        # is not the last instruction
        if len(pc_list) >= 8 and pc_list[-8]["op"] == "CALLVALUE":
            # reference to CALLVALUE 8 instructions previous is a nonpayable function check
            pc_list[-1].update(
                dev="Cannot send ether to nonpayable function",
                fn=pc_list[-8].get("fn", "<unknown>"),
                offset=pc_list[-8].get("offset"),
                path=pc_list[-8].get("path"),
            )
            return

    # if there is active function, we are still in the function selector table
    if not fn_node:
        return

    # get the offset of the next instruction
    next_offset = None
    if source_map and source_map[0][2] != -1:
        next_offset = (source_map[0][0], source_map[0][0] + source_map[0][1])

    # if the next instruction offset is not equal to the offset of the active function,
    # but IS contained within the active function, apply this offset to the current
    # instruction

    if (
        next_offset
        and next_offset != fn_node.offset
        and is_inside_offset(next_offset, fn_node.offset)
    ):
        pc_list[-1].update(path=str(source_node.contract_id), fn=fn_name, offset=next_offset)
        return

    # if any of the previous conditions are not satisfied, this is the final revert
    # statement within a function
    if fn_node[-1].nodeType == "ExpressionStatement":
        expr = fn_node[-1].expression

        if expr.nodeType == "FunctionCall" and expr.get("expression.name") in ("revert", "require"):
            pc_list[-1].update(
                path=str(source_node.contract_id), fn=fn_name, offset=expr.expression.offset
            )


def _set_invalid_error_string(source_node: NodeBase, pc_map: Dict) -> None:
    # set custom error string for INVALID opcodes
    try:
        node = source_node.children(include_children=False, offset_limits=pc_map["offset"])[0]
    except IndexError:
        return
    node_type: str = node.nodeType
    if node_type == "IndexAccess":
        pc_map["dev"] = "Index out of range"
    elif node_type == "BinaryOperation":
        operator = node.operator
        if operator == "/":
            pc_map["dev"] = "Division by zero"
        elif operator == "%":
            pc_map["dev"] = "Modulus by zero"


def _get_active_fn(source_node: NodeBase, offset: Tuple[int, int]) -> Tuple[NodeBase, str]:
    fn_node = source_node.children(
        depth=2, required_offset=offset, filters={"nodeType": "FunctionDefinition"}
    )[0]
    name = getattr(fn_node, "name", None)
    if not name:
        if getattr(fn_node, "kind", "function") != "function":
            name = f"<{fn_node.kind}>"
        elif getattr(fn_node, "isConstructor", False):
            name = "<constructor>"
        else:
            name = "<fallback>"

    parent = fn_node.parent()
    if parent.nodeType == "SourceUnit":
        # the function exists outside a contract
        return fn_node, name

    return fn_node, f"{fn_node.parent().name}.{name}"


def _get_nodes(output_json: Dict) -> Tuple[List[NodeBase], StatementNodes, BranchNodes]:
    source_nodes: List[NodeBase] = solcast.from_standard_output(output_json)
    stmt_nodes = _get_statement_nodes(source_nodes)
    branch_nodes = _get_branch_nodes(source_nodes)
    return source_nodes, stmt_nodes, branch_nodes


def _get_statement_nodes(source_nodes: List[NodeBase]) -> StatementNodes:
    # Given a list of source nodes, returns a dict of lists of statement nodes
    return {
        str(node.contract_id): {
            i.offset
            for i in node.children(
                include_parents=False,
                filters={"baseNodeType": "Statement"},
                exclude_filter={"isConstructor": True},
            )
        }
        for node in source_nodes
    }


def _get_branch_nodes(source_nodes: List[NodeBase]) -> BranchNodes:
    # Given a list of source nodes, returns a dict of lists of nodes corresponding
    # to possible branches in the code
    branches: BranchNodes = {}
    for node in source_nodes:
        contract_branches: Set[NodeBase] = set()
        branches[str(node.contract_id)] = contract_branches
        for contract_node in node.children(depth=1, filters={"nodeType": "ContractDefinition"}):
            for i in contract_node:
                for child_node in i.children(
                    filters=(
                        {"nodeType": "FunctionCall", "expression.name": "require"},
                        {"nodeType": "IfStatement"},
                        {"nodeType": "Conditional"},
                    )
                ):
                    contract_branches |= _get_recursive_branches(child_node)
    return branches


def _get_recursive_branches(base_node: NodeBase) -> Set[NodeBase]:
    node_type = base_node.nodeType

    # if node is IfStatement or Conditional, look only at the condition
    node = base_node if node_type == "FunctionCall" else base_node.condition
    # for IfStatement, jumping indicates evaluating false
    jump_is_truthful = node_type != "IfStatement"

    filters = (
        {"nodeType": "BinaryOperation", "typeDescriptions.typeString": "bool", "operator": "||"},
        {"nodeType": "BinaryOperation", "typeDescriptions.typeString": "bool", "operator": "&&"},
    )
    all_binaries = node.children(include_parents=True, include_self=True, filters=filters)

    # if no BinaryOperation nodes are found, this node is the branch
    if not all_binaries:
        # if node is FunctionCall, look at the first argument
        if node_type == "FunctionCall":
            node = node.arguments[0]
        # some versions of solc do not map IfStatement unary opertions to bytecode
        elif node.nodeType == "UnaryOperation":
            node = node.subExpression
        node.jump = jump_is_truthful
        return {node}

    # look at children of BinaryOperation nodes to find all possible branches
    binary_branches = set()
    for node in (x for i in all_binaries for x in (i.leftExpression, i.rightExpression)):
        if node.children(include_self=True, filters=filters):
            continue
        _jump = jump_is_truthful
        if not _is_rightmost_operation(node, base_node.depth):
            _jump = _check_left_operator(node, base_node.depth)
        if node.nodeType == "UnaryOperation":
            node = node.subExpression
        node.jump = _jump
        binary_branches.add(node)

    return binary_branches


def _is_rightmost_operation(node: NodeBase, depth: int) -> bool:
    # Check if the node is the final operation within the expression
    parents = node.parents(depth, _BINOPS_PARAMS)
    return not any(i.leftExpression == node or node.is_child_of(i.leftExpression) for i in parents)


def _check_left_operator(node: NodeBase, depth: int) -> bool:
    # Find the nearest parent boolean where this node sits on the left side of
    # the comparison, and return True if that node's operator is ||
    parents = node.parents(depth, _BINOPS_PARAMS)

    op = next(
        i for i in parents if i.leftExpression == node or node.is_child_of(i.leftExpression)
    ).operator
    return op == "||"
