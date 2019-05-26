#!/usr/bin/python3

import ast
from hashlib import sha1
import importlib.util
import json
from pathlib import Path

from . import sources
from brownie._config import CONFIG

BUILD_KEYS = [
    'abi',
    'allSourcePaths',
    'ast',
    'bytecode',
    'bytecodeSha1',
    'compiler',
    'contractName',
    'coverageMap',
    'coverageMapTotals',
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

# TODO - this was being checked at load, it can be moved to when testing is started

# def _check_coverage_hashes(self):
#     # remove coverage data where hashes have changed
#     coverage_path = self._path.parent.joinpath('coverage')
#     for coverage_json in list(coverage_path.glob('**/*.json')):
#         try:
#             dependents = json.load(coverage_json.open())['sha1']
#         except json.JSONDecodeError:
#             coverage_json.unlink()
#             continue
#         for path, hash_ in dependents.items():
#             path = Path(path)
#             if path.exists():
#                 if path.suffix != ".json":
#                     if get_ast_hash(path) == hash_:
#                         continue
#                 elif self._build[path.stem]['bytecodeSha1'] == hash_:
#                     continue
#             coverage_json.unlink()
#             break

# def _recursive_unlink(base_path):
#     for path in [Path(i[0]) for i in list(os.walk(base_path))[:0:-1]]:
#         if not list(path.glob('*')):
#             path.rmdir()


def _stem(contract_name):
    return contract_name.replace('.json', '')


def _absolute(contract_name):
    contract_name = _stem(contract_name)
    return _project_path.joinpath('build/contracts/{}.json'.format(contract_name))


_build = {}
_revert_map = {}
_project_path = None


def load(project_path):
    clear()
    global _project_path
    _project_path = Path(project_path)
    for path in list(_project_path.glob('build/contracts/*.json')):
        try:
            build_json = json.load(path.open())
        except json.JSONDecodeError:
            build_json = {}
        if (
            not set(BUILD_KEYS).issubset(build_json) or
            not project_path.joinpath(build_json['sourcePath']).exists()
        ):
            path.unlink()
            continue
        build_json['pcMap'] = dict((int(k), v) for k, v in build_json['pcMap'].items())
        _build[path.stem] = build_json
        _generate_revert_map(build_json['pcMap'])


def add(build_json):
    path = _absolute(build_json['contractName'])
    json.dump(
        build_json,
        path.open('w'),
        sort_keys=True,
        indent=2,
        default=sorted
    )
    _generate_revert_map(build_json['pcMap'])


def contains(contract_name):
    return _stem(contract_name) in _build


def delete(contract_name):
    del _build[_stem(contract_name)]
    _absolute(contract_name).unlink()


def clear():
    global _project_path
    _project_path = None
    _build.clear()
    _revert_map.clear()


def get(contract_name):
    return _build[_stem(contract_name)]


def items():
    return _build.items()


def _generate_revert_map(pcMap):
    for pc, data in [(k, v) for k, v in pcMap.items() if v['op'] in ("REVERT", "INVALID")]:
        revert = [data['path'], data['start'], data['stop'], ""]
        try:
            s = sources.get(data['path'])[data['stop']:]
            err = s[:s.index('\n')]
            err = err[err.index('//')+2:].strip()
            if err.startswith('dev:'):
                revert[-1] = err
                data['dev'] = err
        except (KeyError, ValueError):
            pass
        _revert_map.setdefault(pc, set()).add(tuple(revert))


def get_error_source_from_pc(pc, pad=3):
    if pc not in _revert_map or len(_revert_map[pc]) > 1:
        return None
    revert = next(iter(_revert_map[pc]))
    if revert[0] is False:
        return ""
    return sources.get_highlighted_source(*revert[:3], pad=pad)


def get_dev_revert(pc):
    if pc not in _revert_map or len(_revert_map[pc]) > 1:
        return None
    return next(iter(_revert_map[pc]))[3]


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
