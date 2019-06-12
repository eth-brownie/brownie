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
    'deployedBytecode',
    'deployedSourceMap',
    'dependencies',
    'offset',
    'opcodes',
    'pcMap',
    'sha1',
    'source',
    'sourceMap',
    'sourcePath',
    'type'
]

_build = {}
_revert_map = {}
_project_path = None


def get(contract_name):
    '''Returns build data for the given contract name.'''
    return _build[_stem(contract_name)]


def items(path=None):
    '''Provides an list of tuples as (key,value), similar to calling dict.items.
    If a path is given, only contracts derived from that source file are returned.'''
    if path is None:
        return _build.items()
    return [(k, v) for k, v in _build.items() if v['sourcePath'] == path]


def contains(contract_name):
    '''Checks if the contract name exists in the currently loaded build data.'''
    return _stem(contract_name) in _build


def get_dependents(contract_name):
    '''Returns a list of contract names that the given contract inherits from
    or links to. Used by the compiler when determining which contracts to
    recompile based on a changed source file.'''
    return [k for k, v in _build.items() if contract_name in v['dependencies']]


def get_dev_revert(pc):
    '''Given the program counter from a stack trace that caused a transaction
    to revert, returns the commented dev string (if any).'''
    if pc not in _revert_map or len(_revert_map[pc]) > 1:
        return None
    return next(iter(_revert_map[pc]))[3]


def get_error_source_from_pc(pc, pad=3):
    '''Given the program counter from a stack trace that caused a transaction
    to revert, returns the highlighted relevent source code.'''
    if pc not in _revert_map or len(_revert_map[pc]) > 1:
        return None, None
    revert = next(iter(_revert_map[pc]))
    if revert[0] is False:
        return None, None
    return sources.get_highlighted_source(*revert[:2], pad=pad), revert[2]


def load(project_path):
    '''Loads all build files for the given project path.
    Files that are corrupted or missing required keys will be deleted.

    Args:
        project_path: root path of the project to load.'''
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
        _add(build_json)


def add(build_json):
    '''Adds a build json to the active project. The data is saved in the
    project's build/contracts folder.

    Args:
        build_json - dictionary of build data to add.'''
    path = _absolute(build_json['contractName'])
    json.dump(
        build_json,
        path.open('w'),
        sort_keys=True,
        indent=2,
        default=sorted
    )
    _add(build_json)


def delete(contract_name):
    '''Removes a contract's build data from the active project.
    The json file in ``build/contracts`` is deleted.

    Args:
        contract_name: name of the contract to delete.'''
    del _build[_stem(contract_name)]
    _absolute(contract_name).unlink()


def clear():
    '''Clears all currently loaded build data.  No files are deleted.'''
    global _project_path
    _project_path = None
    _build.clear()
    _revert_map.clear()


def _add(build_json):
    contract_name = build_json['contractName']
    if "0" in build_json['pcMap']:
        build_json['pcMap'] = dict((int(k), v) for k, v in build_json['pcMap'].items())
    if build_json['compiler']['minify_source']:
        build_json = expand_build_offsets(build_json)
    _build[contract_name] = build_json
    _generate_revert_map(build_json['pcMap'])


def _generate_revert_map(pcMap):
    # {pc: {("path", (start, stop), "function name", "error string" ) .. }}
    for pc, data in [(k, v) for k, v in pcMap.items() if v['op'] in ("REVERT", "INVALID")]:
        _revert_map.setdefault(pc, set())
        if 'fn' not in data:
            _revert_map[pc].add((False, (-1, -1), False, ""))
            continue
        revert = [data['path'], tuple(data['offset']), data['fn'], ""]
        try:
            revert_str = sources.get(data['path'])[data['offset'][1]:]
            revert_str = revert_str[:revert_str.index('\n')]
            revert_str = revert_str[revert_str.index('//')+2:].strip()
            if revert_str.startswith('dev:'):
                revert[-1] = revert_str
                data['dev'] = revert_str
        except (KeyError, ValueError):
            pass
        _revert_map[pc].add(tuple(revert))


def _stem(contract_name):
    return contract_name.replace('.json', '')


def _absolute(contract_name):
    contract_name = _stem(contract_name)
    return _project_path.joinpath('build/contracts/{}.json'.format(contract_name))


def _get_offset(offset_map, name, offset):
    offset = tuple(offset)
    if offset not in offset_map:
        offset_map[offset] = sources.expand_offset(name, offset)
    return offset_map[offset]


def expand_build_offsets(build_json):
    '''Expands minified source offsets in a build json dict.'''
    name = build_json['contractName']
    offset_map = {}

    for value in [v for v in build_json['pcMap'].values() if 'offset' in v]:
        value['offset'] = _get_offset(offset_map, name, value['offset'])

    for key in ('branches', 'statements'):
        coverage_map = build_json['coverageMap'][key]
        for path, fn in [(k, x) for k, v in coverage_map.items() for x in v]:
            value = coverage_map[path][fn]
            coverage_map[path][fn] = dict((
                k,
                _get_offset(offset_map, name, v[:2])+tuple(v[2:])
            ) for k, v in value.items())
    return build_json
