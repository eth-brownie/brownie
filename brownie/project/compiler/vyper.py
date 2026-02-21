#!/usr/bin/python3

import logging
from typing import Final

import semantic_version
import vvm
import vvm.exceptions
import vyper
from eth_typing import ABIElement, HexStr
from packaging.version import Version
from packaging.version import Version as PVersion
from requests.exceptions import ConnectionError
from vyper.cli import vyper_json
from vyper.exceptions import VyperException

from brownie._c_constants import deque
from brownie.exceptions import CompilerError, IncompatibleVyperVersion
from brownie.project import sources
from brownie.project.compiler.utils import VersionList, VersionSpec, expand_source_map
from brownie.project.sources import is_inside_offset
from brownie.typing import (
    Branches,
    BranchMap,
    ContractName,
    InputJsonVyper,
    Offset,
    PcList,
    PCMap,
    ProgramCounter,
    StatementMap,
    Statements,
    VyperAstJson,
    VyperAstNode,
    VyperBuildJson,
)
from brownie.utils import hash_source

vvm_logger: Final = logging.getLogger("vvm")
vvm_logger.setLevel(10)
sh: Final = logging.StreamHandler()
sh.setLevel(10)
sh.setFormatter(logging.Formatter("%(message)s"))
vvm_logger.addHandler(sh)

AVAILABLE_VYPER_VERSIONS: VersionList | None = None
_active_version = Version(vyper.__version__)


EVM_VERSION_MAPPING: Final = [
    ("prague", Version("0.4.3")),
    ("cancun", Version("0.4.0")),
    ("shanghai", Version("0.3.9")),
    ("paris", Version("0.3.7")),
    ("berlin", Version("0.2.12")),
    ("istanbul", Version("0.1.0-beta.16")),
]

_get_installed_vyper_versions: Final = vvm.get_installed_vyper_versions
_get_installable_vyper_versions: Final = vvm.get_installable_vyper_versions
_vvm_set_vyper_version: Final = vvm.set_vyper_version
_vvm_install_vyper: Final = vvm.install_vyper
_vvm_compile_standard: Final = vvm.compile_standard


def get_version() -> Version:
    return _active_version


def set_vyper_version(version: VersionSpec) -> str:
    """Sets the vyper version. If not available it will be installed."""
    global _active_version
    if isinstance(version, str):
        version = Version(version)
    if version != Version(vyper.__version__):
        # NOTE: vvm uses `packaging.version.Version` which is not compatible with
        #       `semantic_version.Version` so we first must cast it as a string
        version_str = str(version)
        try:
            _vvm_set_vyper_version(version_str, silent=True)
        except vvm.exceptions.VyperNotInstalled:
            install_vyper(version)
            _vvm_set_vyper_version(version_str, silent=True)
    _active_version = version
    return str(_active_version)


def get_abi(contract_source: str, name: ContractName) -> dict[ContractName, list[ABIElement]]:
    """
    Given a contract source and name, returns a dict of {name: abi}

    This function is deprecated in favor of `brownie.project.compiler.get_abi`
    """
    input_json: InputJsonVyper = {  # type: ignore [typeddict-item]
        "language": "Vyper",
        "sources": {name: {"content": contract_source}},
        "settings": {"outputSelection": {"*": {"*": ["abi"]}}},
    }
    if _active_version == Version(vyper.__version__):
        try:
            compiled = vyper_json.compile_json(input_json)
        except VyperException as exc:
            raise exc.with_traceback(None)
    else:
        try:
            compiled = _vvm_compile_standard(input_json, vyper_version=str(_active_version))
        except vvm.exceptions.VyperError as exc:
            raise CompilerError(exc, "vyper")

    return {name: compiled["contracts"][name][name]["abi"]}


def _get_vyper_version_list() -> tuple[VersionList, VersionList]:
    global AVAILABLE_VYPER_VERSIONS
    installed_versions = _convert_to_semver(_get_installed_vyper_versions())
    lib_version = Version(vyper.__version__)
    if lib_version not in installed_versions:
        installed_versions.append(lib_version)
    if AVAILABLE_VYPER_VERSIONS is None:
        try:
            AVAILABLE_VYPER_VERSIONS = _convert_to_semver(_get_installable_vyper_versions())
        except ConnectionError:
            if not installed_versions:
                raise ConnectionError("Vyper not installed and cannot connect to GitHub")
            AVAILABLE_VYPER_VERSIONS = installed_versions
    return AVAILABLE_VYPER_VERSIONS, installed_versions


def install_vyper(*versions: str | Version) -> None:
    """Installs vyper versions."""
    for version in versions:
        _vvm_install_vyper(str(version), show_progress=False)


def find_vyper_versions(
    contract_sources: dict[str, str],
    install_needed: bool = False,
    install_latest: bool = False,
    silent: bool = True,
) -> dict[str, list[str]]:
    """
    Analyzes contract pragmas and determines which vyper version(s) to use.

    Args:
        contract_sources: a dictionary in the form of {'path': "source code"}
        install_needed: if True, will install when no installed version matches
                        the contract pragma
        install_latest: if True, will install when a newer version is available
                        than the installed one
        silent: set to False to enable verbose reporting

    Returns: dictionary of {'version': ['path', 'path', ..]}
    """

    available_versions, installed_versions = _get_vyper_version_list()

    pragma_specs: dict[str, semantic_version.NpmSpec] = {}
    to_install: set[str] = set()
    new_versions: set[str] = set()

    for path, source in contract_sources.items():
        pragma_specs[path] = sources.get_vyper_pragma_spec(source, path)
        version = pragma_specs[path].select(installed_versions)

        if not version and not install_needed and not install_latest:
            raise IncompatibleVyperVersion(
                f"No installed vyper version matching '{pragma_specs[path]}' in '{path}'"
            )

        # if no installed version of vyper matches the pragma, find the latest available version
        latest = pragma_specs[path].select(available_versions)

        if not version and not latest:
            raise IncompatibleVyperVersion(
                f"No installable vyper version matching '{pragma_specs[path]}' in '{path}'"
            )

        if not version or (install_latest and latest > version):
            to_install.add(str(latest))
        elif latest and latest > version:
            new_versions.add(str(version))

    # install new versions if needed
    if to_install:
        install_vyper(*to_install)
        _, installed_versions = _get_vyper_version_list()
    elif new_versions and not silent:
        print(
            f"New compatible vyper version{'s' if len(new_versions) > 1 else ''}"
            f" available: {', '.join(new_versions)}"
        )

    # organize source paths by latest available vyper version
    compiler_versions: dict[str, list[str]] = {}
    for path, spec in pragma_specs.items():
        version = spec.select(installed_versions)
        compiler_versions.setdefault(str(version), []).append(path)

    return compiler_versions


def find_best_vyper_version(
    contract_sources: dict[str, str],
    install_needed: bool = False,
    install_latest: bool = False,
    silent: bool = True,
) -> str:
    """
    Analyze contract pragma and find the best compatible version across multiple sources.

    Args:
        contract_sources: a dictionary in the form of {'path': "source code"}
        install_needed: if True, will install when no installed version matches
                        the contract pragma
        install_latest: if True, will install when a newer version is available
                        than the installed one
        silent: set to False to enable verbose reporting

    Returns: version string
    """

    available_versions, installed_versions = _get_vyper_version_list()

    for path, source in contract_sources.items():

        pragma_spec = sources.get_vyper_pragma_spec(source, path)
        installed_versions = [i for i in installed_versions if i in pragma_spec]
        available_versions = [i for i in available_versions if i in pragma_spec]

    if not available_versions:
        raise IncompatibleVyperVersion("No installable vyper version compatible across all sources")

    if not installed_versions and not install_needed and not install_latest:
        raise IncompatibleVyperVersion("No installed vyper version compatible across all sources")

    if max(available_versions) > max(installed_versions, default=Version("0.0.0")):
        if install_latest or (install_needed and not installed_versions):
            install_vyper(max(available_versions))
            return str(max(available_versions))
        if not silent:
            print(f"New compatible vyper version available: {max(available_versions)}")

    return str(max(installed_versions))


def compile_from_input_json(
    input_json: InputJsonVyper, silent: bool = True, allow_paths: str | None = None
) -> dict:
    """
    Compiles contracts from a standard input json.

    Args:
        input_json: vyper input json
        silent: verbose reporting
        allow_paths: compiler allowed filesystem import path

    Returns: standard compiler output json
    """

    version = get_version()
    if not silent:
        print("Compiling contracts...")
        print(f"  Vyper version: {version}")
    if version < Version("0.1.0-beta.17"):
        outputs = input_json["settings"]["outputSelection"]["*"]["*"]
        outputs.remove("userdoc")
        outputs.remove("devdoc")
    if version == Version(vyper.__version__):
        try:
            return vyper_json.compile_json(input_json)
        except VyperException as exc:
            raise exc.with_traceback(None)
    else:
        try:
            # NOTE: vvm uses `packaging.version.Version` which is not compatible with
            #       `semantic_version.Version` so we first must cast it as a string
            version = str(version)
            return _vvm_compile_standard(input_json, base_path=allow_paths, vyper_version=version)
        except vvm.exceptions.VyperError as exc:
            raise CompilerError(exc, "vyper")


def _get_unique_build_json(
    output_evm: dict,
    path_str: str,
    contract_name: ContractName,
    ast_json: dict | list,
    offset: Offset,
) -> VyperBuildJson:

    ast: list = ast_json["body"] if isinstance(ast_json, dict) else ast_json
    deployed_bytecode: dict = output_evm["deployedBytecode"]
    pc_map, statement_map, branch_map = _generate_coverage_data(
        deployed_bytecode["sourceMap"],
        deployed_bytecode["opcodes"],
        contract_name,
        ast,
    )
    bytecode_json: dict = output_evm["bytecode"]
    bytecode: HexStr = bytecode_json["object"]
    # This is not a complete VyperBuildJson object but that's okay for now
    # TODO: make a partial VyperBuildJson subclass for this dtype
    return {  # type: ignore [typeddict-item]
        "allSourcePaths": {"0": path_str},
        "bytecode": bytecode,
        "bytecodeSha1": hash_source(bytecode),
        "coverageMap": {"statements": statement_map, "branches": branch_map},
        "dependencies": _get_dependencies(ast),
        "offset": offset,
        "pcMap": pc_map,
        "type": "contract",
    }


def _get_dependencies(ast_json: list[dict]) -> list[ContractName]:
    return sorted(
        {
            i["name"].split(".")[-1]
            for i in ast_json
            if i["ast_type"] == "Import"
            or (i["ast_type"] == "ImportFrom" and i["module"] != "vyper.interfaces")
        }
    )


def _is_revert_jump(pc_list: PcList, revert_pc: int) -> bool:
    return pc_list[-1]["op"] == "JUMPI" and int(pc_list[-2].get("value", "0"), 16) == revert_pc


def _generate_coverage_data(
    source_map_str: str,
    opcodes_str: str,
    contract_name: ContractName,
    ast_json: VyperAstJson,
) -> tuple[PCMap, StatementMap, BranchMap]:
    if not opcodes_str:
        return PCMap({}), {}, {}
        return {}, {}, {}

    source_map = deque(expand_source_map(source_map_str))
    opcodes = deque(opcodes_str.split(" "))

    fn_nodes = [i for i in ast_json if i["ast_type"] == "FunctionDef"]
    fn_offsets = {i["name"]: _convert_src(i["src"]) for i in fn_nodes}
    stmt_nodes = {_convert_src(i["src"]) for i in _get_statement_nodes(fn_nodes)}

    statement_map: Statements = {}
    branch_map: Branches = {}

    pc_list: PcList = []
    count, pc = 0, 0

    revert_pc = -1
    if opcodes[-5] == "JUMPDEST" and opcodes[-1] == "REVERT":
        # starting in vyper 0.2.14, reverts without a reason string are optimized
        # with a jump to the end of the bytecode. if the bytecode ends with this
        # pattern, we set `revert_pc` as the program counter of the jumpdest so
        # we can identify these optimizer reverts within traces.
        revert_pc = len(opcodes) + sum(int(i[4:]) - 1 for i in opcodes if i.startswith("PUSH")) - 5

    while opcodes and source_map:

        # format of source is [start, stop, contract_id, jump code]
        start, stop, _, jump_code = source_map.popleft()

        op = opcodes.popleft()
        this: ProgramCounter = {"op": op, "pc": pc}  # type: ignore [typeddict-item]
        pc_list.append(this)

        if jump_code != "-":
            this["jump"] = jump_code

        pc += 1
        if opcodes and opcodes[0][:2] == "0x":
            this["value"] = opcodes.popleft()
            pc += int(op[4:])

        # set source offset (-1 means none)
        if start == -1:
            if (len(pc_list) > 6 and pc_list[-7]["op"] == "CALLVALUE" and op == "REVERT") or (
                len(pc_list) > 2
                and pc_list[-3]["op"] == "CALLVALUE"
                and _is_revert_jump(pc_list[-2:], revert_pc)
            ):
                # special case - initial nonpayable check on vyper >=0.2.5
                this["dev"] = "Cannot send ether to nonpayable function"
                # hackiness to prevent the source highlight from showing the entire contract
                if op == "REVERT":
                    # for REVERT, apply to the previous opcode
                    pc_list[-2].update(path="0", offset=(0, 0))  # type: ignore [call-arg]
                else:
                    # for JUMPI we need the mapping on the actual opcode
                    this.update(path="0", offset=(0, 0))  # type: ignore [call-arg]
            continue

        offset: Offset = (start, start + stop)  # type: ignore [assignment]
        this["path"] = "0"
        this["offset"] = offset

        try:
            if "offset" in pc_list[-2] and offset == pc_list[-2]["offset"]:
                this_fn = this["fn"] = pc_list[-2]["fn"]
            else:
                # statement coverage
                fn = next(k for k, v in fn_offsets.items() if is_inside_offset(offset, v))
                this_fn = this["fn"] = f"{contract_name}.{fn}"
                stmt_offset = next(i for i in stmt_nodes if is_inside_offset(offset, i))
                stmt_nodes.remove(stmt_offset)
                statement_map.setdefault(this_fn, {})[count] = stmt_offset
                this["statement"] = count
                count += 1
        except (KeyError, IndexError, StopIteration):
            pass

        if op not in ("JUMPI", "REVERT"):
            continue

        node = _find_node_by_offset(ast_json, offset)
        if node is None:
            continue

        node_ast_type = node["ast_type"]
        if op == "REVERT" or _is_revert_jump(pc_list[-2:], revert_pc):
            # custom revert error strings
            if node_ast_type == "FunctionDef":
                if (op == "REVERT" and pc_list[-7]["op"] == "CALLVALUE") or (
                    op == "JUMPI" and pc_list[-3]["op"] == "CALLVALUE"
                ):
                    this["dev"] = "Cannot send ether to nonpayable function"
            elif node_ast_type == "Subscript":
                this["dev"] = "Index out of range"
            elif node_ast_type in ("AugAssign", "BinOp"):
                node_op: VyperAstNode = node["op"]
                node_op_ast_type = node_op["ast_type"]
                if node_op_ast_type == "Sub":
                    this["dev"] = "Integer underflow"
                elif node_op_ast_type == "Div":
                    this["dev"] = "Division by zero"
                elif node_op_ast_type == "Mod":
                    this["dev"] = "Modulo by zero"
                else:
                    this["dev"] = "Integer overflow"
            continue

        if node_ast_type in ("Assert", "If") or (
            node_ast_type == "Expr"
            and node["value"].get("func", {}).get("id") == "assert_modifiable"
        ):
            # branch coverage
            this["branch"] = count
            this_fn = this["fn"]
            branch_map.setdefault(this_fn, {})  # type: ignore [arg-type]
            if node_ast_type == "If":
                branch_map[this_fn][count] = _convert_src(node["test"]["src"]) + (False,)  # type: ignore [index]
            else:
                branch_map[this_fn][count] = offset + (True,)  # type: ignore [index]
            count += 1

    first = pc_list[0]
    first["path"] = "0"
    first["offset"] = (0, _convert_src(ast_json[-1]["src"])[1])
    if revert_pc != -1:
        this["optimizer_revert"] = True

    pc_map = PCMap({i.pop("pc"): i for i in pc_list})

    return pc_map, {"0": statement_map}, {"0": branch_map}


def _convert_src(src: str) -> Offset:
    if src is None:
        return -1, -1
    split = src.split(":")[:2]
    start = int(split[0])
    stop = start + int(split[1])
    return start, stop


def _find_node_by_offset(ast_json: VyperAstJson, offset: Offset) -> VyperAstNode | None:
    for node in ast_json:
        converted_src = _convert_src(node["src"])
        if is_inside_offset(offset, converted_src):
            if converted_src == offset:
                return node
            node_list: VyperAstJson = [
                i for i in node.values() if isinstance(i, dict) and "ast_type" in i  # type: ignore [misc]
            ]
            for v in node.values():
                if isinstance(v, list):
                    node_list.extend(v)
            if node_list:
                result = _find_node_by_offset(node_list, offset)
            else:
                result = _find_node_by_offset(ast_json[ast_json.index(node) + 1 :], offset)
            if result is not None:
                return result
    return None


def _get_statement_nodes(ast_json: VyperAstJson) -> VyperAstJson:
    stmt_nodes = []
    for node in ast_json:
        if children := [x for v in node.values() if isinstance(v, list) for x in v]:
            stmt_nodes += _get_statement_nodes(children)
        else:
            stmt_nodes.append(node)
    return stmt_nodes


def _convert_to_semver(versions: list[PVersion]) -> VersionList:
    """
    Converts a list of `packaging.version.Version` objects to a list of
    `semantic_version.Version` objects.

    vvm 0.2.0 switched to packaging.version but we are not ready to
    migrate brownie off of semantic-version.

    This function serves as a stopgap.
    """
    return [ 
        Version(
            str(
                semantic_version.Version(
                    major=version.major,
                    minor=version.minor,
                    patch=version.micro,
                    prerelease="".join(str(x) for x in version.pre) if version.pre else None,
                )
            )
        )
        for version in versions
    ]
