#!/usr/bin/python3

from copy import deepcopy
from hashlib import sha1
import json
from pathlib import Path
import re
import solcx

from brownie.exceptions import CompilerError
from brownie.test.coverage import get_coverage_map
import brownie._config
CONFIG = brownie._config.CONFIG

_changed = {}
_contracts = {}

STANDARD_JSON = {
    'language': "Solidity",
    'sources': {},
    'settings': {
        'outputSelection': {'*': {
            '*': [
                "abi",
                "evm.assembly",
                "evm.bytecode",
                "evm.deployedBytecode"
            ],
            '': ["ast"]
        }},
        "optimizer": {
            "enabled": CONFIG['solc']['optimize'],
            "runs": CONFIG['solc']['runs']
        }
    }
}

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


def _check_changed(build, filename, contract, clear=None):
    if contract in _changed:
        return _changed[contract]
    build = build.joinpath('{}.json'.format(contract))
    if not build.exists():
        _changed[contract] = True
        return True
    try:
        CONFIG['solc']['version'] = solcx.get_solc_version_string().strip('\n')
        compiled = json.load(build.open())
        if (
            not set(BUILD_KEYS).issubset(compiled) or
            compiled['compiler'] != CONFIG['solc'] or
            compiled['sha1'] != sha1(filename.open('rb').read()).hexdigest()
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
    coverage_folder = Path(CONFIG['folders']['project']).joinpath("build/coverage")
    for coverage_json in list(coverage_folder.glob('**/*.json')):
        dependents = json.load(coverage_json.open())['sha1']
        for path, hash_ in dependents.items():
            path = Path(path)
            if not path.exists() or sha1(path.open('rb').read()).hexdigest() != hash_:
                print(path)
                coverage_json.unlink()
                break

def compile_contracts(folder):
    '''
    Compiles the project with solc and saves the results
    in the build/contracts folder.
    '''
    if _contracts:
        return deepcopy(_contracts)

    _check_coverage_hashes()

    solcx.set_solc_version(CONFIG['solc']['version'])
    folder = Path(folder).resolve()
    build_folder = folder.parent.joinpath('build/contracts')
    contract_files = [
        i for i in list(folder.glob('**/*.sol')) if
        "_" not in (i.name[0], i.parent.name[0])
    ]
    if not contract_files:
        return {}
    compiler_info = CONFIG['solc'].copy()
    compiler_info['version'] = solcx.get_solc_version_string().strip('\n')
    inheritance_map = {}
    for filename in contract_files:
        code = filename.open().read()
        for name in (
            re.findall(
                "\n(?:contract|library|interface) (.*?){", code, re.DOTALL)
        ):
            names = [i.strip(',') for i in name.strip().split(' ')]
            if names[0] in inheritance_map:
                raise ValueError(
                    "Multiple contracts named {}".format(names[0]))
            inheritance_map[names[0]] = set(names[2:])
            _check_changed(build_folder, filename, names[0])
    for i in range(len(inheritance_map)):
        for base, inherited in [
            (k, x) for k, v in inheritance_map.copy().items() if v for x in v
        ]:
            inheritance_map[base] |= inheritance_map[inherited]
    to_compile = []
    for path in [i for i in build_folder.glob('*.json') if i.stem not in inheritance_map]:
        # remove build files for contracts that no longer exist
        path.unlink()
    for filename in contract_files:
        code = filename.open().read()
        input_json = {}
        for name in (re.findall(
                "\n(?:contract|library|interface) (.*?)[ {]", code, re.DOTALL
        )):
            check = [i for i in inheritance_map[name]
                     if _check_changed(build_folder, filename, i)]
            if not check and not _check_changed(build_folder, filename, name):
                _contracts[name] = json.load(build_folder.joinpath(name+'.json').open())
                continue
            to_compile.append(filename)
            break
    if not to_compile:
        return deepcopy(_contracts)
    print("Compiling contracts...")
    print("Optimizer: {}".format(
        "Enabled  Runs: "+str(CONFIG['solc']['runs']) if
        CONFIG['solc']['optimize'] else "Disabled"
    ))
    print("\n".join(" - {}...".format(i.name) for i in to_compile))
    input_json = STANDARD_JSON.copy()
    input_json['sources'] = dict((str(i), {'content': i.open().read()}) for i in to_compile)
    build_json = _compile_and_format(input_json)
    for name, data in build_json.items():
        json.dump(
            data,
            build_folder.joinpath("{}.json".format(name)).open('w'),
            sort_keys=True,
            indent=4,
            default=sorted
        )
    _contracts.update(build_json)
    return deepcopy(_contracts)


def compile_source(source):
    input_json = STANDARD_JSON.copy()
    input_json['sources'] = {"<string>": {'content': source}}
    return _compile_and_format(input_json)


def get_build(name):
    return deepcopy(_contracts[name])

def _compile_and_format(input_json):
    try:
        compiled = solcx.compile_standard(
            input_json,
            optimize=CONFIG['solc']['optimize'],
            optimize_runs=CONFIG['solc']['runs'],
            allow_paths="."
        )
    except solcx.exceptions.SolcError as e:
        raise CompilerError(e)
    compiled = generate_pcMap(compiled)
    result = {}
    compiler_info = CONFIG['solc'].copy()
    compiler_info['version'] = solcx.get_solc_version_string().strip('\n')
    for filename in input_json['sources']:
        for match in re.findall(
            "\n(?:contract|library|interface) [^ {]{1,}",
            input_json['sources'][filename]['content']
        ):
            type_, name = match.strip('\n').split(' ')
            data = compiled['contracts'][filename][name]
            evm = data['evm']
            if not evm['bytecode']['object']:
                # do not save build files for interfaces or ABCs
                continue
            ref = [
                (k, x) for v in evm['bytecode']['linkReferences'].values()
                for k, x in v.items()
            ]
            for n, loc in [(i[0], x['start']*2) for i in ref for x in i[1]]:
                evm['bytecode']['object'] = "{}__{:_<36}__{}".format(
                    evm['bytecode']['object'][:loc],
                    n[:36],
                    evm['bytecode']['object'][loc+40:]
                )
            result[name] = {
                'abi': data['abi'],
                'ast': compiled['sources'][filename]['ast'],
                'bytecode': evm['bytecode']['object'],
                'compiler': compiler_info,
                'contractName': name,
                'deployedBytecode': evm['deployedBytecode']['object'],
                'deployedSourceMap': evm['deployedBytecode']['sourceMap'],
                'networks': {},
                'opcodes': evm['deployedBytecode']['opcodes'],
                'sha1': sha1(input_json['sources'][filename]['content'].encode()).hexdigest(),
                'source': input_json['sources'][filename]['content'],
                'sourceMap': evm['bytecode']['sourceMap'],
                'sourcePath': filename,
                'type': type_,
                'pcMap': evm['pcMap'],
                'allSourcePaths': sorted(set(i['contract'] for i in evm['pcMap'] if i['contract']))
            }
            result[name]['coverageMap'] = get_coverage_map(result[name])
    return result


def generate_pcMap(compiled):
    '''
    Generates an expanded sourceMap useful for debugging.
    [{
        'contract': relative path of the contract source code
        'jump': jump instruction as supplied in the sourceMap (-,i,o)
        'op': opcode string
        'pc': program counter as given by debug_traceTransaction
        'start': source code start offset
        'stop': source code stop offset
        'value': value of the instruction, if any
    }, ... ]
    '''
    id_map = dict((v['id'], k) for k, v in compiled['sources'].items())
    for filename, name in [(k, x) for k, v in compiled['contracts'].items() for x in v]:
        bytecode = compiled['contracts'][filename][name]['evm']['deployedBytecode']

        if not bytecode['object']:
            compiled['contracts'][filename][name]['evm']['pcMap'] = []
            continue
        pcMap = []
        opcodes = bytecode['opcodes']
        source_map = bytecode['sourceMap']
        while True:
            try:
                i = opcodes[:-1].rindex(' STOP')
            except ValueError:
                break
            if 'JUMPDEST' in opcodes[i:]:
                break
            opcodes = opcodes[:i+5]
        opcodes = opcodes.split(" ")[::-1]
        pc = 0
        last = source_map.split(';')[0].split(':')
        for i in range(3):
            last[i] = int(last[i])
        pcMap.append({
            'start': last[0],
            'stop': last[0]+last[1],
            'op': opcodes.pop(),
            'contract': id_map[last[2]],
            'jump': last[3],
            'pc': 0
        })
        pcMap[0]['value'] = opcodes.pop()
        for value in source_map.split(';')[1:]:
            pc += 1
            if pcMap[-1]['op'][:4] == "PUSH":
                pc += int(pcMap[-1]['op'][4:])
            if value:
                value = (value+":::").split(':')[:4]
                for i in range(3):
                    value[i] = int(value[i] or last[i])
                value[3] = value[3] or last[3]
                last = value
            pcMap.append({
                'start': last[0],
                'stop': last[0]+last[1],
                'op': opcodes.pop(),
                'contract': id_map[last[2]] if last[2] != -1 else False,
                'jump': last[3],
                'pc': pc
            })
            if opcodes[-1][:2] == "0x":
                pcMap[-1]['value'] = opcodes.pop()
        compiled['contracts'][filename][name]['evm']['pcMap'] = pcMap
    return compiled
