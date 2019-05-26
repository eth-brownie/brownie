#!/usr/bin/python3

import json
from pathlib import Path

from . import sources

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
    'dependencies',
    'fn_offsets',
    'offset',
    'opcodes',
    'pcMap',
    'sha1',
    'source',
    'sourceMap',
    'sourcePath',
    'type'
]


def _stem(contract_name):
    return contract_name.replace('.json', '')


def _absolute(contract_name):
    contract_name = _stem(contract_name)
    return _project_path.joinpath('build/contracts/{}.json'.format(contract_name))


_build = {}
_revert_map = {}
_project_path = None


def get(contract_name):
    return _build[_stem(contract_name)]


def items():
    return _build.items()


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
