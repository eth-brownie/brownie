#!/usr/bin/python3

from collections import deque
from hashlib import sha1
from typing import Dict, List, Optional, Tuple

import vyper
from semantic_version import Version
from vyper.cli import vyper_json

from brownie.project.compiler.utils import expand_source_map
from brownie.project.sources import is_inside_offset


def get_version() -> Version:
    return Version.coerce(vyper.__version__)


def get_abi(contract_source: str, name: str) -> Dict:
    """Given a contract source and name, returns a dict of {name: abi}"""
    compiled = vyper_json.compile_json(
        {
            "language": "Vyper",
            "sources": {name: {"content": contract_source}},
            "settings": {"outputSelection": {"*": {"*": ["abi"]}}},
        }
    )
    return {name: compiled["contracts"][name][name]["abi"]}


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

    if not silent:
        print("Compiling contracts...")
        print(f"  Vyper version: {get_version()}")
    return vyper_json.compile_json(input_json, root_path=allow_paths)


def _get_unique_build_json(
    output_evm: Dict, path_str: str, contract_name: str, ast_json: List, offset: Tuple
) -> Dict:
    pc_map, statement_map, branch_map = _generate_coverage_data(
        output_evm["deployedBytecode"]["sourceMap"],
        output_evm["deployedBytecode"]["opcodes"],
        path_str,
        contract_name,
        ast_json,
    )
    return {
        "allSourcePaths": [path_str],
        "bytecode": output_evm["bytecode"]["object"],
        "bytecodeSha1": sha1(output_evm["bytecode"]["object"].encode()).hexdigest(),
        "coverageMap": {"statements": statement_map, "branches": branch_map},
        "dependencies": _get_dependencies(ast_json),
        "offset": offset,
        "pcMap": pc_map,
        "type": "contract",
    }


def _get_dependencies(ast_json: List) -> List:
    import_nodes = [i for i in ast_json if i["ast_type"] == "Import"]
    import_nodes += [
        i for i in ast_json if i["ast_type"] == "ImportFrom" if i["module"] != "vyper.interfaces"
    ]
    return sorted(set([i["names"][0]["name"].split(".")[-1] for i in import_nodes]))


def _generate_coverage_data(
    source_map_str: str, opcodes_str: str, source_str: str, contract_name: str, ast_json: List
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

    while opcodes:
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
            continue
        offset = (source[0], source[0] + source[1])
        pc_list[-1]["path"] = source_str
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
        if pc_list[-1]["op"] == "REVERT":
            # custom revert error strings
            if node["ast_type"] == "FunctionDef" and pc_list[-7]["op"] == "CALLVALUE":
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
            and node["value"]["func"].get("id", None) == "assert_modifiable"
        ):
            # branch coverage
            pc_list[-1]["branch"] = count
            branch_map.setdefault(pc_list[-1]["fn"], {})
            if node["ast_type"] == "If":
                branch_map[pc_list[-1]["fn"]][count] = _convert_src(node["test"]["src"]) + (False,)
            else:
                branch_map[pc_list[-1]["fn"]][count] = offset + (True,)
            count += 1

    pc_list[0]["path"] = source_str
    pc_list[0]["offset"] = [0, _convert_src(ast_json[-1]["src"])[1]]
    pc_map = dict((i.pop("pc"), i) for i in pc_list)

    return pc_map, {source_str: statement_map}, {source_str: branch_map}


def _convert_src(src: str) -> Tuple[int, int]:
    if src is None:
        return -1, -1
    src_int = [int(i) for i in src.split(":")[:2]]
    return src_int[0], src_int[0] + src_int[1]


def _find_node_by_offset(ast_json: List, offset: Tuple) -> Dict:
    node = next(i for i in ast_json if is_inside_offset(offset, _convert_src(i["src"])))
    if _convert_src(node["src"]) == offset:
        return node
    node_list = [i for i in node.values() if isinstance(i, dict) and "ast_type" in i]
    node_list.extend([x for i in node.values() if isinstance(i, list) for x in i])
    return _find_node_by_offset(node_list, offset)


def _get_statement_nodes(ast_json: List) -> List:
    stmt_nodes: List = []
    for node in ast_json:
        children = [x for v in node.values() if isinstance(v, list) for x in v]
        if children:
            stmt_nodes += _get_statement_nodes(children)
        else:
            stmt_nodes.append(node)
    return stmt_nodes
