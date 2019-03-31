#!/usr/bin/python3

from hashlib import sha1
import json
import os
import re
import solcx
import sys
import time

from lib.services import config
CONFIG = config.CONFIG
solcx.set_solc_version(CONFIG['solc']['version'])

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


def _check_changed(filename, contract, clear=None):
    if contract in _changed:
        return _changed[contract]
    json_file = 'build/contracts/{}.json'.format(contract)
    if not os.path.exists(json_file):
        _changed[contract] = True
        return True
    try:
        CONFIG['solc']['version'] = solcx.get_solc_version_string().strip('\n')
        compiled = json.load(open(json_file, encoding="utf-8"))
        if (
            compiled['compiler'] != CONFIG['solc'] or
            compiled['sha1'] != sha1(open(filename, 'rb').read()).hexdigest()
        ):
            _changed[contract] = True
            return True
        _changed[contract] = False
        return False
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        _changed[contract] = True
        return True


def _json_load(filename):
    try:
        return json.load(open("build/contracts/"+filename, encoding="utf-8"))
    except json.JSONDecodeError: 
        raise OSError(
            "'build/contracts/"+filename+"' appears to be corrupted. Delete it"
            " and restart Brownie to fix this error. If this problem persists "
            "you may need to delete your entire build/contracts folder."
        )

def clear_persistence(network_name):
    for filename in os.listdir("build/contracts"):
        compiled = _json_load(filename)
        networks = dict(
            (k, v) for k, v in compiled['networks'].items()
            if 'persist' in CONFIG['networks'][v['network']] and
            CONFIG['networks'][v['network']]['persist'] and
            v['network'] != network_name
        )
        if networks != compiled['networks']:
            compiled['networks'] = networks
            json.dump(
                compiled,
                open("build/contracts/"+filename, 'w', encoding="utf-8"),
                sort_keys=True,
                indent=4
            )


def add_contract(name, address, txid, owner):
    json_file = "build/contracts/{}.json".format(name)
    _contracts[name]['networks'][str(int(time.time()))] = {
        'address': address,
        'transactionHash': txid,
        'network': CONFIG['active_network']['name'],
        'owner': owner}
    json.dump(
        _contracts[name],
        open(json_file, 'w', encoding="utf-8"),
        sort_keys=True,
        indent=4
    )


def compile_contracts(folder = "contracts"):
    '''
    Compiles the project with solc and saves the results
    in the build/contracts folder.
    '''
    if _contracts:
        return _contracts
    clear_persistence(None)
    contract_files = [
        "{}/{}".format(i[0], x) for i in os.walk(folder) for x in i[2]
    ]
    if not contract_files:
        sys.exit("ERROR: Cannot find any .sol files in contracts folder")
    msg = False
    compiler_info = CONFIG['solc'].copy()
    compiler_info['version'] = solcx.get_solc_version_string().strip('\n')

    inheritance_map = {}
    for filename in contract_files:
        code = open(filename, encoding="utf-8").read()
        for name in (
            re.findall(
                "\n(?:contract|library|interface) (.*?){", code, re.DOTALL)
        ):
            names = [i.strip(',') for i in name.strip().split(' ')]
            if names[0] in inheritance_map:
                raise ValueError(
                    "Multiple contracts named {}".format(names[0]))
            inheritance_map[names[0]] = set(names[2:])
            _check_changed(filename, names[0])

    for i in range(len(inheritance_map)):
        for base, inherited in [
            (k, x) for k, v in inheritance_map.copy().items() if v for x in v
        ]:
            inheritance_map[base] |= inheritance_map[inherited]
    to_compile = []
    for filename in contract_files:
        code = open(filename).read()
        input_json = {}
        for name in (re.findall(
                "\n(?:contract|library|interface) (.*?)[ {]", code, re.DOTALL
        )):
            check = [i for i in inheritance_map[name]
                     if _check_changed(filename, i)]
            if not check and not _check_changed(filename, name):
                _contracts[name] = _json_load(name+".json")
                continue
            if not msg:
                print("Compiling contracts...")
                print("Optimizer: {}".format(
                    "Enabled  Runs: "+str(CONFIG['solc']['runs']) if
                    CONFIG['solc']['optimize'] else "Disabled"
                ))
                msg = True
            print(" - {}...".format(filename.split('/')[-1]))
            to_compile.append(filename)
            # input_json = {
            #     'language': "Solidity",
            #     'sources': {
            #         filename: {
            #             'content': open(filename, encoding="utf-8").read()
            #         }
            #     },
            #     'settings': {
            #         'outputSelection': {'*': {
            #             '*': [
            #                 "abi",
            #                 "evm.assembly",
            #                 "evm.bytecode",
            #                 "evm.deployedBytecode"
            #             ],
            #             '': ["ast"]}},
            #         "optimizer": {
            #             "enabled": CONFIG['solc']['optimize'],
            #             "runs": CONFIG['solc']['runs']}
            #     }
            # }
            break
        #if not input_json:
        #    continue
        #print(" - {}...".format(filename.split('/')[-1]))
    if not to_compile:
        return _contracts
    input_json = STANDARD_JSON.copy()
    input_json['sources'] = dict((i,{'content':open(i).read()}) for i in to_compile)
    try:
        compiled = solcx.compile_standard(
            input_json,
            optimize=CONFIG['solc']['optimize'],
            optimize_runs=CONFIG['solc']['runs'],
            allow_paths="."
        )
    except solcx.exceptions.SolcError as e:
        err = json.loads(e.stdout_data)
        print("\nUnable to compile {}:\n".format(filename))
        for i in err['errors']:
            print(i['formattedMessage'])
        sys.exit(1)
#    print(compiled)
    print(compiled['contracts'].keys())
    
    # TODO
    # iterate compiled['contracts'] and save
    # integrate compile_contracts with compile_source
    # expose in console
    # document

    sys.exit(1)
    hash_ = sha1(open(filename, 'rb').read()).hexdigest()
    compiled = generate_pcMap(compiled)
    for match in (
        re.findall("\n(?:contract|library|interface) [^ {]{1,}", code)
    ):
        type_, name = match.strip('\n').split(' ')
        data = compiled['contracts'][filename][name]
        json_file = "build/contracts/{}.json".format(name)
        evm = data['evm']
        ref = [(k, x) for v in evm['bytecode']['linkReferences'].values()
                for k, x in v.items()]
        for n, loc in [(i[0],x['start']*2) for i in ref for x in i[1]]:
            evm['bytecode']['object'] = "{}__{:_<36}__{}".format(
                evm['bytecode']['object'][:loc],
                n[:36],
                evm['bytecode']['object'][loc+40:]
            )
        _contracts[name] = {
            'abi': data['abi'],
            'ast': compiled['sources'][filename]['ast'],
            'bytecode': evm['bytecode']['object'],
            'compiler': compiler_info,
            'contractName': name,
            'deployedBytecode': evm['deployedBytecode']['object'],
            'deployedSourceMap': evm['deployedBytecode']['sourceMap'],
            'networks': {},
            'opcodes': evm['deployedBytecode']['opcodes'],
            'sha1': hash_,
            'source': input_json['sources'][filename]['content'],
            'sourceMap': evm['bytecode']['sourceMap'],
            'sourcePath': filename,
            'type': type_,
            'pcMap': evm['deployedBytecode']['pcMap']
        }
        json.dump(
            _contracts[name],
            open(json_file, 'w', encoding="utf-8"),
            sort_keys=True,
            indent=4
        )
    return _contracts


def compile_source(source, filename="<string>"):
    input_json = {
        'language': "Solidity",
        'sources': {
            filename: {
                'content': source
            }
        },
        'settings': {
            'outputSelection': {'*': {
                '*': [
                    "abi",
                    "evm.assembly",
                    "evm.bytecode",
                    "evm.deployedBytecode"
                ],
                '': ["ast"]}},
            "optimizer": {
                "enabled": CONFIG['solc']['optimize'],
                "runs": CONFIG['solc']['runs']}
        }
    }
    try:
        compiled = solcx.compile_standard(
            input_json,
            optimize=CONFIG['solc']['optimize'],
            optimize_runs=CONFIG['solc']['runs'],
            allow_paths="."
        )
    except solcx.exceptions.SolcError as e:
        err = json.loads(e.stdout_data)
        print("\nUnable to compile {}:\n".format(filename))
        for i in err['errors']:
            print(i['formattedMessage'])
        return {}
    compiled = generate_pcMap(compiled)
    result = {}
    compiler_info = CONFIG['solc'].copy()
    compiler_info['version'] = solcx.get_solc_version_string().strip('\n')
    for match in (
        re.findall("\n(?:contract|library|interface) [^ {]{1,}", source)
    ):
        type_, name = match.strip('\n').split(' ')
        data = compiled['contracts'][filename][name]
        json_file = "build/contracts/{}.json".format(name)
        evm = data['evm']
        ref = [(k, x) for v in evm['bytecode']['linkReferences'].values()
                for k, x in v.items()]
        for n, loc in [(i[0],x['start']*2) for i in ref for x in i[1]]:
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
            'sha1': sha1(source.encode()).hexdigest(),
            'source': input_json['sources'][filename]['content'],
            'sourceMap': evm['bytecode']['sourceMap'],
            'sourcePath': filename,
            'type': type_,
            'pcMap': evm['deployedBytecode']['pcMap']
        }
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
    id_map = dict((v['id'],k) for k,v in compiled['sources'].items())
    for filename, name in [(k,x) for k,v in compiled['contracts'].items() for x in v]:
        bytecode = compiled['contracts'][filename][name]['evm']['deployedBytecode']
    
        if not bytecode['object']:
            bytecode['pcMap'] = []
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
                'contract': id_map[last[2]] if last[2]!=-1 else False,
                'jump': last[3],
                'pc': pc
            })
            if opcodes[-1][:2] == "0x":
                pcMap[-1]['value'] = opcodes.pop()
        bytecode['pcMap'] = pcMap
    return compiled