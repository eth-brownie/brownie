#!/usr/bin/python3

from copy import deepcopy
import json
from pathlib import Path
import re

from . import _sha_compare as compare
from . import compiler
from brownie.types.types import _Singleton
from brownie._config import CONFIG

BUILD_FOLDERS = [
    "build",
    "build/contracts",
    "build/coverage",
    "build/networks"
]


def _check_coverage_hashes():
    # remove coverage data where hashes have changed
    coverage_path = Path(CONFIG['folders']['project']).joinpath("build/coverage")
    for coverage_json in list(coverage_path.glob('**/*.json')):
        dependents = json.load(coverage_json.open())['sha1']
        for path, hash_ in dependents.items():
            path = Path(path)
            if path.suffix != ".json":
                if compare.compare_ast_hash(path, hash_):
                    continue
            elif compare.compare_bytecode_hash(path, hash_):
                continue
            coverage_json.unlink()
            break


def _check_build_paths():
    path = Path(CONFIG['folders']['project']).resolve()
    for folder in [i for i in BUILD_FOLDERS]:
        path.joinpath(folder).mkdir(exist_ok=True)


class Build(metaclass=_Singleton):

    def __init__(self):
        self._build = {}
        self._path = None

    def _load(self):
        self. _path = Path(CONFIG['folders']['project']).joinpath('build/contracts')
        # check build paths
        _check_build_paths()
        # load existing build data
        self._load_build_data()
        # check for changed contracts, recompile
        changed = self._get_changed_contracts()
        # TODO - you are here
        # issue - changed is now a list of contract names, not filenames
        
        if changed:
            build_json = compiler.compile_contracts(changed)
            for name, data in build_json.items():
                json.dump(
                    data,
                    self._path.joinpath("{}.json".format(name)).open('w'),
                    sort_keys=True,
                    indent=4,
                    default=sorted
                )
            self._build.update(build_json)
        # check for changed tests
        _check_coverage_hashes()

    def _load_build_data(self):
        for path in list(self._path.glob('*.json')):
            try:
                build_json = json.load(path.open())
                if (
                    set(BUILD_KEYS).issubset(build_json) and
                    Path(build_json['sourcePath']).exists()
                ):
                    self._build[path.stem] = build_json
                    continue
            except json.JSONDecodeError:
                pass
             path.unlink()

    def _get_changed_contracts():
        path = Path(CONFIG['folders']['project']).joinpath('contracts')
        inheritance_map = compiler.get_inheritance_map(path)
        changed = [i for i in inheritance_map if self._compare_build_json(i)]
        final = set(changed)
        for name, inherited in inheritance_map.items():
            if inherited.intersection(changed):
                final.add(name)
        for name in [i for i in final if i in self._build]:
            self._path.joinpath(name+'.json').unlink()
            del self._build[name]
        return final

    def _compare_build_json(name):
        if name not in self._build:
            return True
        build_json = self._build[name]

        return (
            self._build[name]['compiler'] != CONFIG['solc'] or
            self._build[name]['sha1'] != sha1(open(self._build[name]['sourcePath'],'rb').read()).hexdigest()
        )

    def contracts(self):
        return deepcopy(self._build).items()

    def get_contract(self, name):
        return deepcopy(self._build[name])
