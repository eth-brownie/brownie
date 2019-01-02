#!/usr/bin/python3

from eth_abi import decode_abi, decode_single
from hexbytes import HexBytes
import json
import os
import solc
from subprocess import Popen, DEVNULL
import sys
import time
from web3 import Web3, HTTPProvider

from lib.components import config


class VirtualMachineError(Exception):

    def __init__(self,e):
        msg = eval(str(e))['message']
        if len(msg.split('revert ',maxsplit=1))>1:
            self.revert_msg = msg.split('revert ')[1]
        else:
            self.revert_msg = None
        super().__init__(msg)

class web3:

    _rpc = None
    
    def __init__(self, verbose = True):
        name = config['active_network']
        try:
            netconf = config['networks'][name]
            if verbose:
                print("Using network '{}'".format(name))
        except KeyError:
            sys.exit("ERROR: Network '{}' is not defined in config.json".format(name))
        if self._rpc:
            if verbose:
                print("Resetting environment...")
            self._rpc.terminate()
        if 'test-rpc' in netconf:
            if verbose:
                print("Running '{}'...".format(netconf['test-rpc']))
            self._rpc = Popen(
                netconf['test-rpc'].split(' '),
                stdout = DEVNULL,
                stdin = DEVNULL,
                stderr = DEVNULL)
        web3 = Web3(HTTPProvider(netconf['host']))
        for i in range(20):
            if web3.isConnected():
                break
            if i == 19:
               raise ConnectionError("Could not connect to {}".format(netconf['host']))
            time.sleep(0.2)
        for name, fn in [(i,getattr(web3,i)) for i in dir(web3) if i[0].islower()]:
            setattr(self, name, fn)

    def __del__(self):
        if self._rpc:
            self._rpc.terminate()

    def _reset(self, verbose = True):
        self.__init__(verbose)


class TransactionReceipt:

    gas_profiles = {}
    
    def __init__(self, txid, silent=False, name=None):
        self.fn_name = name
        while True:
            tx = web3.eth.getTransaction(txid)
            if tx: break
            time.sleep(0.5)
        if config['logging']['tx'] and not silent:
            print("\nTransaction sent: {}".format(txid.hex()))
        for k,v in tx.items():
            setattr(self, k, v.hex() if type(v) is HexBytes else v)
        if not tx.blockNumber and CONFIG['logging']['tx'] and not silent:
            print("Waiting for confirmation...")
        receipt = web3.eth.waitForTransactionReceipt(txid)
        for k,v in [(k,v) for k,v in receipt.items() if k not in tx]:
            if type(v) is HexBytes:
                v = v.hex()
            setattr(self, k, v)
        if name and '--gas' in sys.argv:
            self.gas_profiles.setdefault(name,{'avg':0,'high':0,'low':float('inf'),'count':0})
            gas = self.gas_profiles[name]
            gas['avg'] = (gas['avg']*gas['count']+receipt.gasUsed)/(gas['count']+1)
            gas['count']+=1
            gas['high'] = max(gas['high'],receipt.gasUsed)
            gas['low'] = min(gas['low'],receipt.gasUsed)
        if silent:
            return
        if config['logging']['tx'] >= 2:
            self.info()
        elif config['logging']['tx']:
            print("Transaction confirmed - block: {}   gas spent: {}".format(
                receipt.blockNumber, receipt.gasUsed))
            if not self.contractAddress: return
            print("Contract deployed at: {}".format(self.contractAddress))
    
    def info(self):
        print("""
Transaction was Mined
---------------------
Tx Hash: {0.hash}
From: {0.from}
{1}{2}
Block: {0.blockNumber}
Gas Used: {0.gasUsed}
""".format(
    self,
    ("New Contract Address: "+self.contractAddress if self.contractAddress
     else "To: {0.to}\nValue: {0.value}".format(self)),
    "\nFunction: {}".format(self.fn_name) if (self.input!="0x00" and not self.contractAddress) else ""))
    
        if self.logs:
            print("  Events In This Transaction\n  ---------------------------")
            for event in self.logs:
                data = _decode_event(event)
                print("  "+data['name'])
                for i in data['data']:
                    print("    {0[key]}: {0[value]}".format(i))
            print()

    def __repr__(self):
        return "<Transaction object '{}'>".format(self.hash)


def wei(value):
    if value is None:
        return 0
    if type(value) is float and "e+" in str(value):
        num, dec = str(value).split("e+")
        num = num.split(".") if "." in num else [num, ""]
        return int(num[0] + num[1][:int(dec)] + "0" * (int(dec) - len(num[1])))
    if type(value) is not str or " " not in value:
        return int(value)
    for unit, dec in UNITS.items():
        if " " + unit not in value:
            continue
        num = value.split(" ")[0]
        num = num.split(".") if "." in num else [num, ""]
        return int(num[0] + num[1][:int(dec)] + "0" * (int(dec) - len(num[1])))
    try:
        return int(value)
    except ValueError:
        raise ValueError("Unknown denomination: {}".format(value))    

def add_contract(name, address, txid, owner):
    json_file = config['folders']['project']+'/build/contracts/{}.json'.format(name)
    data = COMPILED[name]
    data['networks'][str(int(time.time()))] = {
        'address': address,
        'transactionHash': txid,
        'network': config['active_network'],
        'owner': owner }
    json.dump(COMPILED[name], open(json_file, 'w'), sort_keys=True, indent=4)

def compile_contracts(clear_network = None):
    contract_files = ["{}/{}".format(i[0],x) for i in os.walk(config['folders']['project']+'/contracts') for x in i[2]] 
    if not contract_files:
        sys.exit("ERROR: Cannot find any .sol files in contracts folder")
    msg = False
    compiler_info = config['solc'].copy()
    compiler_info['version'] = solc.get_solc_version_string().strip('\n')
    final = {}
    for filename in contract_files:
        names = [[x.strip('\t') for x in i.split(' ') if x]
                 for i in open(filename).readlines()]
        for name in [i[1] for i in names if i[0] in ("contract", "library")]:
            json_file = config['folders']['project']+'/build/contracts/{}.json'.format(name)
            if os.path.exists(json_file):
                try:
                    compiled = json.load(open(json_file))
                    if (compiled['compiler'] == compiler_info and
                        compiled['updatedAt'] >= os.path.getmtime(filename)):
                        networks = dict(
                            (k,v) for k,v in compiled['networks'].items()
                            if 'persist' in config['networks'][v['network']] and 
                            config['networks'][v['network']]['persist'] and
                            v['network'] != clear_network)
                        if networks != compiled['networks']:
                            compiled['networks'] = networks
                            json.dump(compiled, open(json_file, 'w'),
                                      sort_keys = True, indent = 4)
                        final[name] = compiled
                        continue
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
            if not msg:
                print("Compiling contracts...\n Optimizer: {}".format("Enabled   Runs: {}".format(
                      config['solc']['runs']) if config['solc']['optimize'] else "Disabled"))
                msg = True
            input_json = {
                'language': "Solidity",
                'sources': {filename: {'content': open(filename).read()}},
                'settings': {
                    'outputSelection': {'*': {
                        '*': ["abi", "evm.bytecode", "evm.deployedBytecode"],
                        '': ["ast", "legacyAST"] } },
                    "optimizer": {
                        "enabled": config['solc']['optimize'],
                        "runs": config['solc']['runs'] }
                }
            }
            print(" - {}...".format(name))
            try:
                compiled = solc.compile_standard(
                    input_json,
                    optimize = config['solc']['optimize'],
                    optimize_runs = config['solc']['runs'],
                    allow_paths = ".")
            except solc.exceptions.SolcError as e:
                err = json.loads(e.stdout_data)
                print("\nERROR: Unable to compile {} due to the following errors:\n".format(filename))
                for i in err['errors']:
                    print(i['formattedMessage'])
                sys.exit()
            for name, data in compiled['contracts'][filename].items():
                json_file = config['folders']['project']+'/build/contracts/{}.json'.format(name)
                evm = data['evm']
                final[name] = {
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
                json.dump(final[name], open(json_file, 'w'),
                          sort_keys=True, indent=4)
            break
    global COMPILED
    COMPILED = final
    return final


def _decode_event(event):
    topic = TOPICS[event.topics[0].hex()]
    result = {'name':topic['name'], 'data':[]}
    types = [i['type'] if i['type']!="bytes" else "bytes[]" for i in topic['inputs'] if not i['indexed']]
    decoded = list(decode_abi(types, HexBytes(event.data)))[::-1]
    topics = event.topics[:0:-1]
    for i in topic['inputs']:
        value = decode_single(i['type'], topics.pop()) if i['indexed'] else decoded.pop()
        if type(value) is bytes:
            value = web3.toHex(value)
        result['data'].append({'key': i['name'], 'value': value})
    return result

def _generate_topics():
    try:
        topics = json.load(open(config['folders']['brownie']+"/topics.json", 'r'))
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        topics = {}
    events = [x for i in COMPILED.values() for x in i['abi'] if x['type']=="event"]
    for i in events:
        key = web3.sha3(text="{}({})".format(
            i['name'], ",".join(x['type'] for x in i['inputs']))).hex()
        topics[key] = {'name':i['name'], 'inputs':i['inputs']}
    json.dump(
        topics, open(config['folders']['brownie']+"/topics.json", 'w'),
        sort_keys=True, indent=4
    )
    return topics


web3 = web3()
UNITS = {
    'kwei': 3, 'babbage': 3, 'mwei': 6, 'lovelace': 6, 'gwei': 9, 'shannon': 9,
    'microether': 12, 'szabo': 12, 'milliether': 15, 'finney': 15, 'ether': 18 }
COMPILED = compile_contracts()
TOPICS = _generate_topics()
