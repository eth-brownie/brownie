#!/usr/bin/python3

import ast
from hashlib import sha1
import importlib.util
import json
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
        # check for changed tests
        self._check_coverage_hashes()

    def _load_build_data(self):
        for path in list(self._path.glob('*.json')):
            try:
                build_json = json.load(path.open())
                if (
                    set(BUILD_KEYS).issubset(build_json) and
                    Path(build_json['sourcePath']).exists()
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

    def _check_coverage_hashes(self):
        # remove coverage data where hashes have changed
        coverage_path = self._path.parent.joinpath('coverage')
        for coverage_json in list(coverage_path.glob('**/*.json')):
            dependents = json.load(coverage_json.open())['sha1']
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
