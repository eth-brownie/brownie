#!/usr/bin/python3

from copy import deepcopy
from hashlib import sha1
import json
from pathlib import Path
import re

import brownie.utils.compiler as compiler
import brownie._config as config
CONFIG = config.CONFIG

BUILD_FOLDERS = ["build", "build/contracts", "build/coverage", "build/networks"]

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


_changed = {}




def compile_source(source):
    result = []
    for name, build in compiler.compile_source(source).items():
        if build['type'] == "interface":
            continue
        result.append(ContractContainer(build))
    return result


def _get_changed_contracts():
    path = Path(CONFIG['folders']['project'])
    build_path = path.joinpath('build/contracts')
    contract_files = [
        i for i in path.glob('contracts/**/*.sol') if "/_" not in str(i)
    ]
    inheritance_map = compiler.get_inheritance_map(contract_files)
    changed = []
    for filename in contract_files:
        code = filename.open().read()
        input_json = {}
        for name in (re.findall(
                "\n(?:contract|library|interface) (.*?)[ {]", code, re.DOTALL
        )):
            check = [i for i in inheritance_map[name]
                     if _check_changed(i)]
            if not check and not _check_changed(name):
                continue
            changed.append(filename)
            break
    return changed


def _check_changed(contract):

    build_path = Path(CONFIG['folders']['project']).joinpath('build/contracts')
    if contract in _changed:
        return _changed[contract]
    build = build_path.joinpath('{}.json'.format(contract))
    if not build.exists():
        _changed[contract] = True
        return True
    try:
        compiled = json.load(build.open())
        if (
            not set(BUILD_KEYS).issubset(compiled) or
            compiled['compiler'] != CONFIG['solc'] or
            compiled['sha1'] != sha1(open(compiled['sourcePath'],'rb').read()).hexdigest()
        ):
            _changed[contract] = True
            return True
        _changed[contract] = False
        return False
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        _changed[contract] = True
        return True


def _check_coverage_hashes():
    # remove coverage data where hashes have changed
    coverage_path = Path(CONFIG['folders']['project']).joinpath("build/coverage")
    for coverage_json in list(coverage_path.glob('**/*.json')):
        dependents = json.load(coverage_json.open())['sha1']
        for path, hash_ in dependents.items():
            path = Path(path)
            try:
                if path.suffix != ".json":
                    if sha1(path.open('rb').read()).hexdigest() == hash_:
                        continue
                elif sha1(json.load(
                    # hash of bytecode without final metadata
                    path.open())['bytecode'][:-68].encode()
                ).hexdigest() == hash_:
                    continue
            except Exception:
                pass
            coverage_json.unlink()
            break


class Build:

    def __init__(self):
        self._path = None
        self._build = {}

    def _load(self):
        self._path = Path(CONFIG['folders']['project']).resolve()
        for folder in [i for i in BUILD_FOLDERS]:
            self._path.joinpath(folder).mkdir(exist_ok=True)
        build_path = self._path.joinpath('build/contracts')
        changed = _get_changed_contracts()
        if changed:
            build_json = compiler.compile_contracts(changed)
            for name, data in build_json.items():
                json.dump(
                    data,
                    build_path.joinpath("{}.json".format(name)).open('w'),
                    sort_keys=True,
                    indent=4,
                    default=sorted
                )
            self._build = build_json
        for path in list(build_path.glob('*.json')):
            if path.name in self._build:
                continue
            build_json = json.load(path.open())
            if not Path(build_json['sourcePath']).exists():
                path.unlink()
                continue
            self._build[path.stem] = build_json
        _check_coverage_hashes()

    def contracts(self):
        return deepcopy(self._build).items()

    def get_contract(self, name):
        return deepcopy(self._build[name])
