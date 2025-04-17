#!/usr/bin/python3

import logging
from collections import deque
from hashlib import sha1
from typing import Dict, List, Optional, Tuple, Union

import vvm
import vyper
from packaging.version import Version as PVersion
from requests.exceptions import ConnectionError
from semantic_version import Version
from vyper.cli import vyper_json
from vyper.exceptions import VyperException

from brownie.exceptions import CompilerError, IncompatibleVyperVersion
from brownie.project import sources
from brownie.project.compiler.utils import expand_source_map
from brownie.project.sources import is_inside_offset

vvm_logger = logging.getLogger("vvm")
vvm_logger.setLevel(10)
sh = logging.StreamHandler()
sh.setLevel(10)
sh.setFormatter(logging.Formatter("%(message)s"))
vvm_logger.addHandler(sh)

AVAILABLE_VYPER_VERSIONS = None
_active_version = Version(vyper.__version__)


EVM_VERSION_MAPPING = [
    ("shanghai", Version("0.3.9")),
    ("paris", Version("0.3.7")),
    ("berlin", Version("0.2.12")),
    ("istanbul", Version("0.1.0-beta.16")),
]


def get_version() -> Version:
    return _active_version


def set_vyper_version(version: Union[str, Version]) -> str:
    """Sets the vyper version. If not available it will be installed."""
    global _active_version
    if isinstance(version, str):
        version = Version(version)
    if version != Version(vyper.__version__):
        # NOTE: vvm uses `packaging.version.Version` which is not compatible with
        #       `semantic_version.Version` so we first must cast it as a string
        version_str = str(version)
        try:
            vvm.set_vyper_version(version_str, silent=True)
        except vvm.exceptions.VyperNotInstalled:
            install_vyper(version)
            vvm.set_vyper_version(version_str, silent=True)
    _active_version = version
    return str(_active_version)


def get_abi(contract_source: str, name: str) -> Dict:
    """
    Given a contract source and name, returns a dict of {name: abi}

    This function is deprecated in favor of `brownie.project.compiler.get_abi`
    """
    input_json = {
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
            compiled = vvm.compile_standard(input_json, vyper_version=str(_active_version))
        except vvm.exceptions.VyperError as exc:
            raise CompilerError(exc, "vyper")

    return {name: compiled["contracts"][name][name]["abi"]}


def _get_vyper_version_list() -> Tuple[List, List]:
    global AVAILABLE_VYPER_VERSIONS
    installed_versions = _convert_to_semver(vvm.get_installed_vyper_versions())
    lib_version = Version(vyper.__version__)
    if lib_version not in installed_versions:
        installed_versions.append(lib_version)
    if AVAILABLE_VYPER_VERSIONS is None:
        try:
            AVAILABLE_VYPER_VERSIONS = _convert_to_semver(vvm.get_installable_vyper_versions())
        except ConnectionError:
            if not installed_versions:
                raise ConnectionError("Vyper not installed and cannot connect to GitHub")
            AVAILABLE_VYPER_VERSIONS = installed_versions
    return AVAILABLE_VYPER_VERSIONS, installed_versions


def install_vyper(*versions: str) -> None:
    """Installs vyper versions."""
    for version in versions:
        vvm.install_vyper(str(version), show_progress=False)


def find_vyper_versions(
    contract_sources: Dict[str, str],
    install_needed: bool = False,
    install_latest: bool = False,
    silent: bool = True,
) -> Dict:
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

    pragma_specs: Dict = {}
    to_install = set()
    new_versions = set()

    for path, source in contract_sources.items():
        pragma_specs[path] = sources.get_vyper_pragma_spec(source, path)
        version = pragma_specs[path].select(installed_versions)

        if not version and not (install_needed or install_latest):
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
    compiler_versions: Dict = {}
    for path, spec in pragma_specs.items():
        version = spec.select(installed_versions)
        compiler_versions.setdefault(str(version), []).append(path)

    return compiler_versions


def find_best_vyper_version(
    contract_sources: Dict[str, str],
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

    if not installed_versions and not (install_needed or install_latest):
        raise IncompatibleVyperVersion("No installed vyper version compatible across all sources")

    if max(available_versions) > max(installed_versions, default=Version("0.0.0")):
        if install_latest or (install_needed and not installed_versions):
            install_vyper(max(available_versions))
            return str(max(available_versions))
        if not silent:
            print(f"New compatible vyper version available: {max(available_versions)}")

    return str(max(installed_versions))


def compile_from_input_json(
    input_json: Dict, silent: bool = True, allow_paths: Optional[str] = None
) -> Dict:
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
            return vvm.compile_standard(input_json, base_path=allow_paths, vyper_version=version)
        except vvm.exceptions.VyperError as exc:
            raise CompilerError(exc, "vyper")


def _get_unique_build_json(
    output_evm: Dict, path_str: str, contract_name: str, ast_json: Union[Dict, List], offset: Tuple
) -> Dict:

    ast: List
    if isinstance(ast_json, dict):
        ast = ast_json["body"]
    else:
        ast = ast_json

    pc_map, statement_map, branch_map = _generate_coverage_data(
        output_evm["deployedBytecode"]["sourceMap"],
        output_evm["deployedBytecode"]["opcodes"],
        contract_name,
        ast,
    )
    return {
        "allSourcePaths": {"0": path_str},
        "bytecode": output_evm["bytecode"]["object"],
        "bytecodeSha1": sha1(output_evm["bytecode"]["object"].encode()).hexdigest(),
        "coverageMap": {"statements": statement_map, "branches": branch_map},
        "dependencies": _get_dependencies(ast),
        "offset": offset,
        "pcMap": pc_map,
        "type": "contract",
    }


def _get_dependencies(ast_json: List) -> List:
    import_nodes = [i for i in ast_json if i["ast_type"] == "Import"]
    import_nodes += [
        i for i in ast_json if i["ast_type"] == "ImportFrom" if i["module"] != "vyper.interfaces"
    ]
    return sorted(set([i["name"].split(".")[-1] for i in import_nodes]))


def _is_revert_jump(pc_list: List, revert_pc: int) -> bool:
    return pc_list[-1]["op"] == "JUMPI" and int(pc_list[-2].get("value", "0"), 16) == revert_pc


def _generate_coverage_data(
    source_map_str: str, opcodes_str: str, contract_name: str, ast_json: List
) -> Tuple:
    if not opcodes_str:
        return {}, {}, {}

    source_map = deque(expand_source_map(source_map_str))
    opcodes = deque(opcodes_str.split(" "))

    fn_nodes = [i for i in ast_json if i["ast_type"] == "FunctionDef"]
    fn_offsets = dict((i["name"], _convert_src(i["src"])) for i in fn_nodes)
    stmt_nodes = set(_convert_src(i["src"]) for i in _get_statement_nodes(fn_nodes))

    statement_map: Dict = {}
    branch_map: Dict = {}

    pc_list: List = []
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
        source = source_map.popleft()
        pc_list.append({"op": opcodes.popleft(), "pc": pc})

        if source[3] != "-":
            pc_list[-1]["jump"] = source[3]

        pc += 1
        if opcodes and opcodes[0][:2] == "0x":
            pc_list[-1]["value"] = opcodes.popleft()
            pc += int(pc_list[-1]["op"][4:])

        # set source offset (-1 means none)
        if source[0] == -1:
            if (
                len(pc_list) > 6
                and pc_list[-7]["op"] == "CALLVALUE"
                and pc_list[-1]["op"] == "REVERT"
            ) or (
                len(pc_list) > 2
                and pc_list[-3]["op"] == "CALLVALUE"
                and _is_revert_jump(pc_list[-2:], revert_pc)
            ):
                # special case - initial nonpayable check on vyper >=0.2.5
                pc_list[-1]["dev"] = "Cannot send ether to nonpayable function"
                # hackiness to prevent the source highlight from showing the entire contract
                if pc_list[-1]["op"] == "REVERT":
                    # for REVERT, apply to the previous opcode
                    pc_list[-2].update(path="0", offset=[0, 0])
                else:
                    # for JUMPI we need the mapping on the actual opcode
                    pc_list[-1].update(path="0", offset=[0, 0])
            continue
        offset = (source[0], source[0] + source[1])
        pc_list[-1]["path"] = "0"
        pc_list[-1]["offset"] = offset

        try:
            if "offset" in pc_list[-2] and offset == pc_list[-2]["offset"]:
                pc_list[-1]["fn"] = pc_list[-2]["fn"]
            else:
                # statement coverage
                fn = next(k for k, v in fn_offsets.items() if is_inside_offset(offset, v))
                pc_list[-1]["fn"] = f"{contract_name}.{fn}"
                stmt_offset = next(i for i in stmt_nodes if is_inside_offset(offset, i))
                stmt_nodes.remove(stmt_offset)
                statement_map.setdefault(pc_list[-1]["fn"], {})[count] = stmt_offset
                pc_list[-1]["statement"] = count
                count += 1
        except (KeyError, IndexError, StopIteration):
            pass

        if pc_list[-1]["op"] not in ("JUMPI", "REVERT"):
            continue

        node = _find_node_by_offset(ast_json, offset)
        if node is None:
            continue

        if pc_list[-1]["op"] == "REVERT" or _is_revert_jump(pc_list[-2:], revert_pc):
            # custom revert error strings
            if node["ast_type"] == "FunctionDef":
                if (pc_list[-1]["op"] == "REVERT" and pc_list[-7]["op"] == "CALLVALUE") or (
                    pc_list[-1]["op"] == "JUMPI" and pc_list[-3]["op"] == "CALLVALUE"
                ):
                    pc_list[-1]["dev"] = "Cannot send ether to nonpayable function"
            elif node["ast_type"] == "Subscript":
                pc_list[-1]["dev"] = "Index out of range"
            elif node["ast_type"] in ("AugAssign", "BinOp"):
                if node["op"]["ast_type"] == "Sub":
                    pc_list[-1]["dev"] = "Integer underflow"
                elif node["op"]["ast_type"] == "Div":
                    pc_list[-1]["dev"] = "Division by zero"
                elif node["op"]["ast_type"] == "Mod":
                    pc_list[-1]["dev"] = "Modulo by zero"
                else:
                    pc_list[-1]["dev"] = "Integer overflow"
            continue

        if node["ast_type"] in ("Assert", "If") or (
            node["ast_type"] == "Expr"
            and node["value"].get("func", {}).get("id", None) == "assert_modifiable"
        ):
            # branch coverage
            pc_list[-1]["branch"] = count
            branch_map.setdefault(pc_list[-1]["fn"], {})
            if node["ast_type"] == "If":
                branch_map[pc_list[-1]["fn"]][count] = _convert_src(node["test"]["src"]) + (False,)
            else:
                branch_map[pc_list[-1]["fn"]][count] = offset + (True,)
            count += 1

    pc_list[0]["path"] = "0"
    pc_list[0]["offset"] = [0, _convert_src(ast_json[-1]["src"])[1]]
    if revert_pc != -1:
        pc_list[-1]["optimizer_revert"] = True

    pc_map = dict((i.pop("pc"), i) for i in pc_list)

    return pc_map, {"0": statement_map}, {"0": branch_map}


def _convert_src(src: str) -> Tuple[int, int]:
    if src is None:
        return -1, -1
    src_int = [int(i) for i in src.split(":")[:2]]
    return src_int[0], src_int[0] + src_int[1]


def _find_node_by_offset(ast_json: List, offset: Tuple) -> Optional[Dict]:
    for node in [i for i in ast_json if is_inside_offset(offset, _convert_src(i["src"]))]:
        if _convert_src(node["src"]) == offset:
            return node
        node_list = [i for i in node.values() if isinstance(i, dict) and "ast_type" in i]
        node_list.extend([x for i in node.values() if isinstance(i, list) for x in i])
        if node_list:
            result = _find_node_by_offset(node_list, offset)
        else:
            result = _find_node_by_offset(ast_json[ast_json.index(node) + 1 :], offset)
        if result is not None:
            return result
    return None


def _get_statement_nodes(ast_json: List) -> List:
    stmt_nodes: List = []
    for node in ast_json:
        children = [x for v in node.values() if isinstance(v, list) for x in v]
        if children:
            stmt_nodes += _get_statement_nodes(children)
        else:
            stmt_nodes.append(node)
    return stmt_nodes


def _convert_to_semver(versions: List[PVersion]) -> List[Version]:
    """
    Converts a list of `packaging.version.Version` objects to a list of
    `semantic_version.Version` objects.

    vvm 0.2.0 switched to packaging.version but we are not ready to
    migrate brownie off of semantic-version.

    This function serves as a stopgap.
    """
    return [
        Version(
            major=version.major,
            minor=version.minor,
            patch=version.micro,
            prerelease="".join(str(x) for x in version.pre) if version.pre else None,
        )
        for version in versions
    ]
