#!/usr/bin/python3

import ast
from hashlib import sha1
import importlib.util
import json
import os
from pathlib import Path

from . import compiler
from .sources import Sources
from brownie.types.types import _Singleton
from brownie._config import CONFIG

BUILD_FOLDERS = [
    "build",
    "build/contracts",
    "build/coverage",
    "build/networks"
]

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

sources = Sources()


class Build(metaclass=_Singleton):

    def __init__(self):
        self._build = {}
        self._path = None

    def __getitem__(self, contract_name):
        return self._build[contract_name.replace('.json', '')]

    def __contains__(self, contract_name):
        return contract_name.replace('.json', '') in self._build

    def _load(self):
        self. _path = Path(CONFIG['folders']['project']).joinpath('build/contracts')
        # check build paths
        _check_build_paths()
        # load existing build data
        self._load_build_data()
        # check for changed contracts, recompile
        changed_paths = self._get_changed_contracts()
        if changed_paths:
            build_json = compiler.compile_contracts(changed_paths)
            for name, data in build_json.items():
                json.dump(
                    data,
                    self._path.joinpath("{}.json".format(name)).open('w'),
                    sort_keys=True,
                    indent=2,
                    default=sorted
                )
            self._build.update(build_json)
        self._generate_revert_map()
        # check for changed tests
        self._check_coverage_hashes()
        _recursive_unlink(str(self._path.parent.joinpath('coverage')))

    def _load_build_data(self):
        project_path = Path(CONFIG['folders']['project'])
        for path in list(self._path.glob('*.json')):
            try:
                build_json = json.load(path.open())
                if (
                    set(BUILD_KEYS).issubset(build_json) and
                    project_path.joinpath(build_json['sourcePath']).exists()
                ):
                    build_json['pcMap'] = dict((int(k), v) for k, v in build_json['pcMap'].items())
                    self._build[path.stem] = build_json
                    continue
            except json.JSONDecodeError:
                pass
            path.unlink()

    def _get_changed_contracts(self):
        inheritance_map = sources.inheritance_map()
        changed = [i for i in inheritance_map if self._compare_build_json(i)]
        final = set(changed)
        for name, inherited in inheritance_map.items():
            if inherited.intersection(changed):
                final.add(name)
        for name in [i for i in final if i in self._build]:
            self._path.joinpath(name+'.json').unlink()
            del self._build[name]
        return set(sources.get_path(i) for i in final)

    def _compare_build_json(self, name):
        return (
            name not in self._build or
            self._build[name]['compiler'] != CONFIG['solc'] or
            self._build[name]['sha1'] != sources.get_hash(name)
        )

    def _generate_revert_map(self):
        self._revert_map = {}
        for pcMap in [v['pcMap'] for v in self._build.values()]:
            for pc, data in [(k, v) for k, v in pcMap.items() if v['op'] in ("REVERT", "INVALID")]:
                revert = [data['contract'], data['start'], data['stop'], ""]
                try:
                    s = sources[data['contract']][data['stop']:]
                    err = s[:s.index('\n')]
                    err = err[err.index('//')+2:].strip()
                    if err.startswith('dev:'):
                        revert[-1] = err
                        data['dev'] = err
                except (KeyError, ValueError):
                    pass
                self._revert_map.setdefault(pc, set()).add(tuple(revert))

    def _check_coverage_hashes(self):
        # remove coverage data where hashes have changed
        coverage_path = self._path.parent.joinpath('coverage')
        for coverage_json in list(coverage_path.glob('**/*.json')):
            try:
                dependents = json.load(coverage_json.open())['sha1']
            except json.JSONDecodeError:
                coverage_json.unlink()
                continue
            for path, hash_ in dependents.items():
                path = Path(path)
                if path.exists():
                    if path.suffix != ".json":
                        if get_ast_hash(path) == hash_:
                            continue
                    elif self._build[path.stem]['bytecodeSha1'] == hash_:
                        continue
                coverage_json.unlink()
                break

    def items(self):
        return self._build.items()

    def get_error_source_from_pc(self, pc, pad=3):
        if pc not in self._revert_map or len(self._revert_map[pc]) > 1:
            return
        if len(self._revert_map[pc]) == len([i for i in self._revert_map[pc] if i[0] is False]):
            return ""
        revert = next(iter(self._revert_map[pc]))
        return sources.get_highlighted_source(*revert[:3], pad=pad)

    def get_dev_revert(self, pc):
        if pc not in self._revert_map or len(self._revert_map[pc]) > 1:
            return None
        if len(self._revert_map[pc]) == len([i for i in self._revert_map[pc] if i[0] is False]):
            return ""
        return next(iter(self._revert_map[pc]))[3]


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


def _check_build_paths():
    path = Path(CONFIG['folders']['project']).resolve()
    for folder in [i for i in BUILD_FOLDERS]:
        path.joinpath(folder).mkdir(exist_ok=True)


def _recursive_unlink(base_path):
    for path in [Path(i[0]) for i in list(os.walk(base_path))[:0:-1]]:
        if not list(path.glob('*')):
            path.rmdir()
