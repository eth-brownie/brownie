#!/usr/bin/python3

import logging
import re
from collections import deque
from copy import deepcopy
from hashlib import sha1
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import solcast
import solcx
from requests.exceptions import ConnectionError
from semantic_version import NpmSpec, Version
from solcast.nodes import NodeBase

from brownie.exceptions import CompilerError, IncompatibleSolcVersion, PragmaError

from . import sources

solcx_logger = logging.getLogger("solcx")
solcx_logger.setLevel(10)
sh = logging.StreamHandler()
sh.setLevel(10)
sh.setFormatter(logging.Formatter("%(message)s"))
solcx_logger.addHandler(sh)

STANDARD_JSON = {
    "language": "Solidity",
    "sources": {},
    "settings": {
        "outputSelection": {
            "*": {"*": ["abi", "evm.assembly", "evm.bytecode", "evm.deployedBytecode"], "": ["ast"]}
        },
        "optimizer": {"enabled": True, "runs": 200},
        "evmVersion": None,
        "remappings": [],
    },
}
PRAGMA_REGEX = re.compile(r"pragma +solidity([^;]*);")
AVAILABLE_SOLC_VERSIONS = None
EVM_SOLC_VERSIONS = [
    # ("istanbul", Version("0.5.13")),  # TODO enable when ganache istanbul support is out of beta
    ("petersburg", Version("0.5.5")),
    ("byzantium", Version("0.4.0")),
]


def set_solc_version(version: str) -> str:
    """Sets the solc version. If not available it will be installed."""
    if Version(version.lstrip("v")) < Version("0.4.22"):
        raise IncompatibleSolcVersion("Brownie only supports Solidity versions >=0.4.22")
    try:
        solcx.set_solc_version(version, silent=True)
    except solcx.exceptions.SolcNotInstalled:
        install_solc(version)
        solcx.set_solc_version(version, silent=True)
    return str(solcx.get_solc_version())


def install_solc(*versions: str) -> None:
    """Installs solc versions."""
    for version in versions:
        solcx.install_solc(str(version))


def compile_and_format(
    contract_sources: Dict[str, str],
    solc_version: Optional[str] = None,
    optimize: bool = True,
    runs: int = 200,
    evm_version: int = None,
    minify: bool = False,
    silent: bool = True,
    allow_paths: Optional[str] = None,
) -> Dict:
    """Compiles contracts and returns build data.

    Args:
        contracts: a dictionary in the form of {'path': "source code"}
        solc_version: solc version to compile with (use None to set via pragmas)
        optimize: enable solc optimizer
        runs: optimizer runs
        evm_version: evm version to compile for
        minify: minify source files
        silent: verbose reporting
        allow_paths: compiler allowed filesystem import path

    Returns:
        build data dict
    """
    if not contract_sources:
        return {}

    if solc_version is not None:
        path_versions = {solc_version: list(contract_sources)}
    else:
        path_versions = find_solc_versions(contract_sources, install_needed=True, silent=silent)

    build_json: Dict = {}
    for version, path_list in path_versions.items():
        set_solc_version(version)
        compiler_data = {"minify_source": minify, "version": str(solcx.get_solc_version())}
        to_compile = dict((k, v) for k, v in contract_sources.items() if k in path_list)

        input_json = generate_input_json(to_compile, optimize, runs, evm_version, minify)
        output_json = compile_from_input_json(input_json, silent, allow_paths)
        build_json.update(generate_build_json(input_json, output_json, compiler_data, silent))
    return build_json


def find_solc_versions(
    contract_sources: Dict[str, str],
    install_needed: bool = False,
    install_latest: bool = False,
    silent: bool = True,
) -> Dict:

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

        pragma_string = next(PRAGMA_REGEX.finditer(source), None)
        if pragma_string is None:
            raise PragmaError(f"No version pragma in '{path}'")
        pragma_specs[path] = NpmSpec(pragma_string.groups()[0])
        version = pragma_specs[path].select(installed_versions)

        if not version and not (install_needed or install_latest):
            raise IncompatibleSolcVersion(
                f"No installed solc version matching '{pragma_string[0]}' in '{path}'"
            )

        # if no installed version of solc matches the pragma, find the latest available version
        latest = pragma_specs[path].select(available_versions)

        if not version and not latest:
            raise IncompatibleSolcVersion(
                f"No installable solc version matching '{pragma_string[0]}' in '{path}'"
            )

        if not version or (install_latest and latest > version):
            to_install.add(latest)
        elif latest > version:
            new_versions.add(str(version))

    # install new versions if needed
    if to_install:
        install_solc(*to_install)
        installed_versions = [Version(i[1:]) for i in solcx.get_installed_solc_versions()]
    elif new_versions and not silent:
        print(
            f"New compatible solc version{'s' if len(new_versions) > 1 else ''}"
            f" available: {', '.join(new_versions)}"
        )

    # organize source paths by latest available solc version
    compiler_versions: Dict = {}
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

    available_versions, installed_versions = _get_solc_version_list()

    for path, source in contract_sources.items():

        pragma_string = next(PRAGMA_REGEX.finditer(source), None)
        if pragma_string is None:
            raise PragmaError(f"No version pragma in '{path}'")
        pragma_spec = NpmSpec(pragma_string.groups()[0])
        installed_versions = [i for i in installed_versions if i in pragma_spec]
        available_versions = [i for i in available_versions if i in pragma_spec]

    if not available_versions:
        raise IncompatibleSolcVersion("No installable solc version compatible across all sources")

    if not installed_versions and not (install_needed or install_latest):
        raise IncompatibleSolcVersion("No installed solc version compatible across all sources")

    if max(available_versions) > max(installed_versions, default=Version("0.0.0")):
        if install_latest or (install_needed and not installed_versions):
            install_solc(max(available_versions))
            return str(max(available_versions))
        if not silent:
            print(f"New compatible solc version available: {max(available_versions)}")

    return str(max(installed_versions))


def _get_solc_version_list() -> Tuple[List, List]:
    global AVAILABLE_SOLC_VERSIONS
    installed_versions = [Version(i[1:]) for i in solcx.get_installed_solc_versions()]
    if AVAILABLE_SOLC_VERSIONS is None:
        try:
            AVAILABLE_SOLC_VERSIONS = [Version(i[1:]) for i in solcx.get_available_solc_versions()]
        except ConnectionError:
            if not installed_versions:
                raise ConnectionError("Solc not installed and cannot connect to GitHub")
            AVAILABLE_SOLC_VERSIONS = installed_versions
    return AVAILABLE_SOLC_VERSIONS, installed_versions


def generate_input_json(
    contract_sources: Dict[str, str],
    optimize: bool = True,
    runs: int = 200,
    evm_version: Union[int, str, None] = None,
    minify: bool = False,
) -> Dict:
    """Formats contracts to the standard solc input json.

    Args:
        contract_sources: a dictionary in the form of {path: 'source code'}
        optimize: enable solc optimizer
        runs: optimizer runs
        evm_version: evm version to compile for
        minify: should source code be minified?

    Returns: dict
    """
    if evm_version is None:
        evm_version = next(i[0] for i in EVM_SOLC_VERSIONS if solcx.get_solc_version() >= i[1])
    input_json: Dict = deepcopy(STANDARD_JSON)
    input_json["settings"]["optimizer"]["enabled"] = optimize
    input_json["settings"]["optimizer"]["runs"] = runs if optimize else 0
    input_json["settings"]["evmVersion"] = evm_version
    input_json["sources"] = dict(
        (k, {"content": sources.minify(v)[0] if minify else v}) for k, v in contract_sources.items()
    )
    return input_json


def compile_from_input_json(
    input_json: Dict, silent: bool = True, allow_paths: Optional[str] = None
) -> Dict:

    """
    Compiles contracts from a standard input json.

    Args:
        input_json: solc input json
        silent: verbose reporting
        allow_paths: compiler allowed filesystem import path

    Returns: standard compiler output json
    """

    optimizer = input_json["settings"]["optimizer"]
    input_json["settings"].setdefault("evmVersion", None)
    if not silent:
        print("Compiling contracts...")
        print(f"  Solc version: {str(solcx.get_solc_version())}")
        print(
            "  Optimizer: "
            + (f"Enabled  Runs: {optimizer['runs']}" if optimizer["enabled"] else "Disabled")
        )
        if input_json["settings"]["evmVersion"]:
            print(f"  EVM Version: {input_json['settings']['evmVersion'].capitalize()}")
    try:
        return solcx.compile_standard(
            input_json,
            optimize=optimizer["enabled"],
            optimize_runs=optimizer["runs"],
            evm_version=input_json["settings"]["evmVersion"],
            allow_paths=allow_paths,
        )
    except solcx.exceptions.SolcError as e:
        raise CompilerError(e)


def generate_build_json(
    input_json: Dict, output_json: Dict, compiler_data: Optional[Dict] = None, silent: bool = True
) -> Dict:
    """Formats standard compiler output to the brownie build json.

    Args:
        input_json: solc input json used to compile
        output_json: output json returned by compiler
        compiler_data: additonal data to include under 'compiler' in build json
        silent: verbose reporting

    Returns: build json dict"""
    if not silent:
        print("Generating build data...")

    if compiler_data is None:
        compiler_data = {}
    compiler_data.update(
        {
            "optimize": input_json["settings"]["optimizer"]["enabled"],
            "runs": input_json["settings"]["optimizer"]["runs"],
            "evm_version": input_json["settings"]["evmVersion"],
        }
    )
    minified = "minify_source" in compiler_data and compiler_data["minify_source"]
    build_json = {}
    path_list = list(input_json["sources"])

    source_nodes = solcast.from_standard_output(output_json)
    statement_nodes = _get_statement_nodes(source_nodes)
    branch_nodes = _get_branch_nodes(source_nodes)

    for path, contract_name in [(k, v) for k in path_list for v in output_json["contracts"][k]]:

        if not silent:
            print(f" - {contract_name}...")

        abi = output_json["contracts"][path][contract_name]["abi"]
        evm = output_json["contracts"][path][contract_name]["evm"]
        bytecode = _format_link_references(evm)
        hash_ = sources.get_hash(input_json["sources"][path]["content"], contract_name, minified)
        node = next(i[contract_name] for i in source_nodes if i.absolutePath == path)
        paths = sorted(
            set([node.parent().absolutePath] + [i.parent().absolutePath for i in node.dependencies])
        )

        pc_map, statement_map, branch_map = _generate_coverage_data(
            evm["deployedBytecode"]["sourceMap"],
            evm["deployedBytecode"]["opcodes"],
            node,
            statement_nodes,
            branch_nodes,
            next((True for i in abi if i["type"] == "fallback"), False),
        )

        build_json[contract_name] = {
            "abi": abi,
            "allSourcePaths": paths,
            "ast": output_json["sources"][path]["ast"],
            "bytecode": bytecode,
            "bytecodeSha1": _get_bytecode_hash(bytecode),
            "compiler": compiler_data,
            "contractName": contract_name,
            "coverageMap": {"statements": statement_map, "branches": branch_map},
            "deployedBytecode": evm["deployedBytecode"]["object"],
            "deployedSourceMap": evm["deployedBytecode"]["sourceMap"],
            "dependencies": [i.name for i in node.dependencies],
            # 'networks': {},
            "offset": node.offset,
            "opcodes": evm["deployedBytecode"]["opcodes"],
            "pcMap": pc_map,
            "sha1": hash_,
            "source": input_json["sources"][path]["content"],
            "sourceMap": evm["bytecode"]["sourceMap"],
            "sourcePath": path,
            "type": node.contractKind,
        }

    if not silent:
        print("")

    return build_json


def _format_link_references(evm: Dict) -> Dict:
    # Standardizes formatting for unlinked libraries within bytecode
    bytecode = evm["bytecode"]["object"]
    references = [(k, x) for v in evm["bytecode"]["linkReferences"].values() for k, x in v.items()]
    for n, loc in [(i[0], x["start"] * 2) for i in references for x in i[1]]:
        bytecode = f"{bytecode[:loc]}__{n[:36]:_<36}__{bytecode[loc+40:]}"
    return bytecode


def _get_bytecode_hash(bytecode: Dict) -> str:
    # Returns a sha1 hash of the given bytecode without metadata
    return sha1(bytecode[:-68].encode()).hexdigest()


def _generate_coverage_data(
    source_map_str: str,
    opcodes_str: str,
    contract_node: Any,
    stmt_nodes: Dict,
    branch_nodes: Dict,
    has_fallback: bool,
) -> Tuple:
    # Generates data used by Brownie for debugging and coverage evaluation
    if not opcodes_str:
        return {}, {}, {}

    source_map = deque(_expand_source_map(source_map_str))
    opcodes = deque(opcodes_str.split(" "))

    contract_nodes = [contract_node] + contract_node.dependencies
    source_nodes = dict((i.contract_id, i.parent()) for i in contract_nodes)
    paths = set(v.absolutePath for v in source_nodes.values())

    stmt_nodes = dict((i, stmt_nodes[i].copy()) for i in paths)
    statement_map: Dict = dict((i, {}) for i in paths)

    # possible branch offsets
    branch_original = dict((i, branch_nodes[i].copy()) for i in paths)
    branch_nodes = dict((i, set(i.offset for i in branch_nodes[i])) for i in paths)
    # currently active branches, awaiting a jumpi
    branch_active: Dict = dict((i, {}) for i in paths)
    # branches that have been set
    branch_set: Dict = dict((i, {}) for i in paths)

    count, pc = 0, 0
    pc_list: List = []
    revert_map: Dict = {}
    fallback_hexstr: str = "unassigned"

    while source_map:

        # format of source is [start, stop, contract_id, jump code]
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
            fallback_hexstr = "0x" + hex(pc - 4).upper()[2:]
            pc_list[-1]["first_revert"] = True

        if source[3] != "-":
            pc_list[-1]["jump"] = source[3]

        pc += 1
        if opcodes[0][:2] == "0x":
            pc_list[-1]["value"] = opcodes.popleft()
            pc += int(pc_list[-1]["op"][4:])

        # set contract path (-1 means none)
        if source[2] == -1:
            if pc_list[-1]["op"] == "REVERT" and pc_list[-8]["op"] == "CALLVALUE":
                pc_list[-1].update(
                    {
                        "dev": "Cannot send ether to nonpayable function",
                        "fn": pc_list[-8].get("fn", "<unknown>"),
                        "offset": pc_list[-8]["offset"],
                        "path": pc_list[-8]["path"],
                    }
                )
            continue
        path = source_nodes[source[2]].absolutePath
        pc_list[-1]["path"] = path

        # set source offset (-1 means none)
        if source[0] == -1:
            continue
        offset = (source[0], source[0] + source[1])
        pc_list[-1]["offset"] = offset

        # add error messages for INVALID opcodes
        if pc_list[-1]["op"] == "INVALID":
            node = source_nodes[source[2]].children(include_children=False, offset_limits=offset)[0]
            if node.nodeType == "IndexAccess":
                pc_list[-1]["dev"] = "Index out of range"
            elif node.nodeType == "BinaryOperation" and node.operator == "/":
                pc_list[-1]["dev"] = "Division by zero"

        # if op is jumpi, set active branch markers
        if branch_active[path] and pc_list[-1]["op"] == "JUMPI":
            for offset in branch_active[path]:
                # ( program counter index, JUMPI index)
                branch_set[path][offset] = (branch_active[path][offset], len(pc_list) - 1)
            branch_active[path].clear()

        # if op relates to previously set branch marker, clear it
        elif offset in branch_nodes[path]:
            if offset in branch_set[path]:
                del branch_set[path][offset]
            branch_active[path][offset] = len(pc_list) - 1

        try:
            # set fn name and statement coverage marker
            if "offset" in pc_list[-2] and offset == pc_list[-2]["offset"]:
                pc_list[-1]["fn"] = pc_list[-2]["fn"]
            else:
                pc_list[-1]["fn"] = _get_fn_full_name(source_nodes[source[2]], offset)
                statement = next(i for i in stmt_nodes[path] if sources.is_inside_offset(offset, i))
                stmt_nodes[path].discard(statement)
                statement_map[path].setdefault(pc_list[-1]["fn"], {})[count] = statement
                pc_list[-1]["statement"] = count
                count += 1
        except (KeyError, IndexError, StopIteration):
            pass
        if "value" not in pc_list[-1]:
            continue
        if pc_list[-1]["value"] == fallback_hexstr and opcodes[0] in {"JUMP", "JUMPI"}:
            # track all jumps to the initial revert
            revert_map.setdefault((pc_list[-1]["path"], pc_list[-1]["offset"]), []).append(
                len(pc_list)
            )

    # compare revert() statements against the map of revert jumps to find
    for (path, fn_offset), values in revert_map.items():
        fn_node = next(i for i in source_nodes.values() if i.absolutePath == path).children(
            depth=2,
            include_children=False,
            required_offset=fn_offset,
            filters={"nodeType": "FunctionDefinition"},
        )[0]
        revert_nodes = fn_node.children(
            filters={"nodeType": "FunctionCall", "expression.name": "revert"}
        )
        # if the node has arguments it will always be included in the source map
        for node in (i for i in revert_nodes if not i.arguments):
            offset = node.offset
            # if the node offset is not in the source map, apply it's offset to the JUMPI op
            if not next((x for x in pc_list if "offset" in x and x["offset"] == offset), False):
                pc_list[values[0]].update({"offset": offset, "jump_revert": True})
                del values[0]

    # set branch index markers and build final branch map
    branch_map: Dict = dict((i, {}) for i in paths)
    for path, offset, idx in [(k, x, y) for k, v in branch_set.items() for x, y in v.items()]:
        # for branch to be hit, need an op relating to the source and the next JUMPI
        # this is because of how the compiler optimizes nested BinaryOperations
        if "fn" not in pc_list[idx[0]]:
            continue
        fn = pc_list[idx[0]]["fn"]
        pc_list[idx[0]]["branch"] = count
        pc_list[idx[1]]["branch"] = count
        node = next(i for i in branch_original[path] if i.offset == offset)
        branch_map[path].setdefault(fn, {})[count] = offset + (node.jump,)
        count += 1

    pc_map = dict((i.pop("pc"), i) for i in pc_list)
    return pc_map, statement_map, branch_map


def _get_fn_full_name(source_node: NodeBase, offset: Tuple[int, int]) -> str:
    node = source_node.children(
        depth=2, required_offset=offset, filters={"nodeType": "FunctionDefinition"}
    )[0]
    name = getattr(node, "name", None)
    if not name:
        if getattr(node, "kind", "function") != "function":
            name = f"<{node.kind}>"
        elif getattr(node, "isConstructor", False):
            name = "<constructor>"
        else:
            name = "<fallback>"
    return f"{node.parent().name}.{name}"


def _expand_source_map(source_map_str: str) -> List:
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


def _get_statement_nodes(source_nodes: Dict) -> Dict:
    # Given a list of source nodes, returns a dict of lists of statement nodes
    statements = {}
    for node in source_nodes:
        statements[node.absolutePath] = set(
            i.offset
            for i in node.children(
                include_parents=False,
                filters={"baseNodeType": "Statement"},
                exclude_filter={"isConstructor": True},
            )
        )
    return statements


def _get_branch_nodes(source_nodes: List) -> Dict:
    # Given a list of source nodes, returns a dict of lists of nodes corresponding
    # to possible branches in the code
    branches: Dict = {}
    for node in source_nodes:
        branches[node.absolutePath] = set()
        for contract_node in node.children(depth=1, filters={"nodeType": "ContractDefinition"}):
            for child_node in [
                x
                for i in contract_node
                for x in i.children(
                    filters=(
                        {"nodeType": "FunctionCall", "expression.name": "require"},
                        {"nodeType": "IfStatement"},
                        {"nodeType": "Conditional"},
                    )
                )
            ]:
                branches[node.absolutePath] |= _get_recursive_branches(child_node)
    return branches


def _get_recursive_branches(base_node: Any) -> Set:
    # if node is IfStatement or Conditional, look only at the condition
    node = base_node if base_node.nodeType == "FunctionCall" else base_node.condition
    # for IfStatement, jumping indicates evaluating false
    jump_is_truthful = base_node.nodeType != "IfStatement"

    filters = (
        {"nodeType": "BinaryOperation", "typeDescriptions.typeString": "bool", "operator": "||"},
        {"nodeType": "BinaryOperation", "typeDescriptions.typeString": "bool", "operator": "&&"},
    )
    all_binaries = node.children(include_parents=True, include_self=True, filters=filters)

    # if no BinaryOperation nodes are found, this node is the branch
    if not all_binaries:
        # if node is FunctionCall, look at the first argument
        if base_node.nodeType == "FunctionCall":
            node = node.arguments[0]
        # some versions of solc do not map IfStatement unary opertions to bytecode
        elif node.nodeType == "UnaryOperation":
            node = node.subExpression
        node.jump = jump_is_truthful
        return set([node])

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
    parents = node.parents(
        depth, {"nodeType": "BinaryOperation", "typeDescriptions.typeString": "bool"}
    )
    return not next(
        (i for i in parents if i.leftExpression == node or node.is_child_of(i.leftExpression)),
        False,
    )


def _check_left_operator(node: NodeBase, depth: int) -> bool:
    # Find the nearest parent boolean where this node sits on the left side of
    # the comparison, and return True if that node's operator is ||
    parents = node.parents(
        depth, {"nodeType": "BinaryOperation", "typeDescriptions.typeString": "bool"}
    )
    op = next(
        i for i in parents if i.leftExpression == node or node.is_child_of(i.leftExpression)
    ).operator
    return op == "||"
