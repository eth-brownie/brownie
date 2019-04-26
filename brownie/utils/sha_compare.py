#!/usr/bin/python3

import ast
from hashlib import sha1
import importlib.util
import json
from pathlib import Path

import brownie._config as config
CONFIG = config.CONFIG

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
    'networks',
    'opcodes',
    'pcMap',
    'sha1',
    'source',
    'sourceMap',
    'sourcePath',
    'type'
]

_changed_build = {}


def compare_build_json(contract):
    if contract in _changed_build:
        return _changed_build[contract]
    build_folder = Path(CONFIG['folders']['project']).joinpath('build/contracts')
    build = build_folder.joinpath('{}.json'.format(contract))
    if not build.exists():
        _changed_build[contract] = True
        return True
    try:
        compiled = json.load(build.open())
        if (
            not set(BUILD_KEYS).issubset(compiled) or
            compiled['compiler'] != CONFIG['solc'] or
            compiled['sha1'] != sha1(open(compiled['sourcePath'],'rb').read()).hexdigest()
        ):
            _changed_build[contract] = True
            return True
        _changed_build[contract] = False
        return False
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        _changed_build[contract] = True
        return True


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
    return get_ast_hash(path) == hash_


def get_bytecode_hash(build_path):
    build_json = json.load(Path(build_path).open())
    # hash of bytecode without final metadata
    return sha1(build_json['bytecode'][:-68].encode()).hexdigest()


def compare_bytecode_hash(build_path, hash_):
    return get_bytecode_hash(build_path) == hash_
