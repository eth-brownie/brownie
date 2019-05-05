#!/usr/bin/python3

import ast
from hashlib import sha1
import importlib.util
import json
from pathlib import Path

from brownie._config import CONFIG

BUILD_KEYS = [
    'abi',
    'allSourcePaths',
    'ast',
    'bytecode',
    'compiler',
    'contractName',
    'coverageMap',
    'deployedBytecode',
    'deployedSourceMap',
    'opcodes',
    'pcMap',
    'sha1',
    'source',
    'sourceMap',
    'sourcePath',
    'type'
]


def get_ast_hash(script_path):
    ast_list = [ast.parse(Path(script_path).open().read())]
    for obj in [i for i in ast_list[0].body if type(i) in (ast.Import, ast.ImportFrom)]:
        if type(obj) is ast.Import:
            name = obj.names[0].name
        else:
            name = obj.module
        origin = importlib.util.find_spec(name).origin
        if CONFIG['folders']['project'] in origin:
            ast_list.append(ast.parse(open(origin).read()))
    dump = "\n".join(ast.dump(i) for i in ast_list)
    return sha1(dump.encode()).hexdigest()


def compare_ast_hash(path, hash_):
    try:
        return get_ast_hash(path) == hash_
    except FileNotFoundError:
        return False


def get_bytecode_hash(build_path):
    build_json = json.load(Path(build_path).open())
    # hash of bytecode without final metadata
    return sha1(build_json['bytecode'][:-68].encode()).hexdigest()


def compare_bytecode_hash(build_path, hash_):
    try:
        return get_bytecode_hash(build_path) == hash_
    except FileNotFoundError:
        return False
