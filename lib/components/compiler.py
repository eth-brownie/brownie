#!/usr/bin/python3

import json
import os
import re
import solc
import sys
import time

from lib.components import config
CONFIG = config.CONFIG
CONFIG['solc']['version'] = solc.get_solc_version_string().strip('\n')

_changed = {}
_contracts = {}

def _check_changed(filename, contract, clear=None):
    if contract in _changed:
        return _changed[contract]
    json_file = 'build/contracts/{}.json'.format(contract)
    if not os.path.exists(json_file):
        _changed[contract] = True
        return True
    try:
        compiled = json.load(open(json_file))
        if (compiled['compiler'] != CONFIG['solc'] or
            compiled['updatedAt'] < os.path.getmtime(filename)):
            _changed[contract] = True
            return True
        _changed[contract] = False
        return False
    except (json.JSONDecodeError, FileNotFoundError):
        _changed[contract] = True
        return True

def clear_persistence(network_name):
    for filename in os.listdir("build/contracts"):
        compiled = json.load(open("build/contracts/"+filename))
        networks = dict(
            (k,v) for k,v in compiled['networks'].items()
            if 'persist' in CONFIG['networks'][v['network']] and 
            CONFIG['networks'][v['network']]['persist'] and
            v['network'] != network_name
        )
        if networks != compiled['networks']:
            compiled['networks'] = networks
            json.dump(
                compiled,
                open("build/contracts/"+filename, 'w'),
                sort_keys=True,
                indent=4
            )


def add_contract(name, address, txid, owner):
    json_file = "build/contracts/{}.json".format(name)
    _contracts[name]['networks'][str(int(time.time()))] = {
        'address': address,
        'transactionHash': txid,
        'network': CONFIG['active_network'],
        'owner': owner }
    json.dump(_contracts[name], open(json_file, 'w'), sort_keys=True, indent=4)


def compile_contracts():
    if _contracts:
        return _contracts
    clear_persistence(None)
    contract_files = ["{}/{}".format(i[0], x) for i in os.walk("contracts") for x in i[2]] 
    if not contract_files:
        sys.exit("ERROR: Cannot find any .sol files in contracts folder")
    msg = False
    compiler_info = CONFIG['solc'].copy()
    compiler_info['version'] = solc.get_solc_version_string().strip('\n')
    
    inheritance_map = {}
    for filename in contract_files:
        code = open(filename).read()
        for name in (
            re.findall("\ncontract (.*?) {", code, re.DOTALL) +
            re.findall('\nlibrary (.*?) {', code, re.DOTALL)
        ):
            if " is " in name:
                name = name.split(' ')
                inheritance_map[name[0]] = set([i.strip(',') for i in name[2:]])
                name = name[0]
            else:
                inheritance_map[name] = set()
            _check_changed(filename, name)

    for i in range(len(inheritance_map)):
        for base, inherited in [(k,x) for k,v in inheritance_map.copy().items() if v for x in v]:
            inheritance_map[base] |= inheritance_map[inherited]
    
    for filename in contract_files:
        code = open(filename).read()
        for name in (
            re.findall("\ncontract (.*?) ", code, re.DOTALL) +
            re.findall('\nlibrary (.*?) ', code, re.DOTALL)
        ):
            check = [i for i in inheritance_map[name] if _check_changed(filename, i)]
            if not check and not _check_changed(filename, name):
                _contracts[name] = json.load(open('build/contracts/{}.json'.format(name)))
                continue
            if not msg:
                print("Compiling contracts...\n Optimizer: {}".format("Enabled   Runs: {}".format(
                      CONFIG['solc']['runs']) if CONFIG['solc']['optimize'] else "Disabled"))
                msg = True
            input_json = {
                'language': "Solidity",
                'sources': {filename: {'content': open(filename).read()}},
                'settings': {
                    'outputSelection': {'*': {
                        '*': ["abi", "evm.bytecode", "evm.deployedBytecode"],
                        '': ["ast", "legacyAST"] } },
                    "optimizer": {
                        "enabled": CONFIG['solc']['optimize'],
                        "runs": CONFIG['solc']['runs'] }
                }
            }
            print(" - {}...".format(name))
            try:
                compiled = solc.compile_standard(
                    input_json,
                    optimize = CONFIG['solc']['optimize'],
                    optimize_runs = CONFIG['solc']['runs'],
                    allow_paths = ".")
            except solc.exceptions.SolcError as e:
                err = json.loads(e.stdout_data)
                print("\nERROR: Unable to compile {} due to the following errors:\n".format(filename))
                for i in err['errors']:
                    print(i['formattedMessage'])
                sys.exit()
            for name, data in compiled['contracts'][filename].items():
                json_file = "build/contracts/{}.json".format(name)
                evm = data['evm']
                _contracts[name] = {
                    'abi': data['abi'],
                    'ast': compiled['sources'][filename]['ast'],
                    'bytecode': evm['bytecode']['object'],
                    'compiler': compiler_info,
                    'contractName': name,
                    'deployedBytecode': evm['deployedBytecode']['object'],
                    'deployedSourceMap': evm['deployedBytecode']['sourceMap'],
                    #'legacyAST': compiled['sources'][filename]['legacyAST'],
                    'networks': {},
                    #'schemaVersion': 0,
                    'source': input_json['sources'][filename]['content'],
                    'sourceMap': evm['bytecode']['sourceMap'],
                    'sourcePath': filename,  
                    'updatedAt': int(time.time())
                }
                json.dump(_contracts[name], open(json_file, 'w'),
                          sort_keys=True, indent=4)
            break
    return _contracts
 