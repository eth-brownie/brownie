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

from lib.components.config import CONFIG, BROWNIE_FOLDER


class VirtualMachineError(Exception):

    def __init__(self,e):
        super().__init__(eval(str(e))['message'])

class web3:

    _rpc = None
    
    def __init__(self):
        name = CONFIG['active_network']
        try:
            netconf = CONFIG['networks'][name]
            print("Using network '{}'".format(name))
        except KeyError:
            sys.exit("ERROR: Network '{}' is not defined in config.json".format(name))
        if self._rpc:
            print("Resetting environment...")
            self._rpc.terminate()
        if 'test-rpc' in netconf:
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

    def _reset(self):
        self.__init__()


class TransactionReceipt:

    def __init__(self, txid):
        
        tx = web3.eth.getTransaction(txid)
        if CONFIG['logging']['tx']:
            print("\nTransaction sent: {}".format(txid.hex()))
        for k,v in tx.items():
            setattr(self, k, v.hex() if type(v) is HexBytes else v)
        if not tx.blockNumber and CONFIG['logging']['tx']:
            print("Waiting for confirmation...")
        receipt = web3.eth.waitForTransactionReceipt(txid)
        for k,v in [(k,v) for k,v in receipt.items() if k not in tx]:
            if type(v) is HexBytes:
                v = v.hex()
            setattr(self, k, v)
        if CONFIG['logging']['tx'] >= 2:
            self.info()
        elif CONFIG['logging']['tx']:
            print("Transaction confirmed - block: {}   gas spent: {}".format(
                tx.blockNumber, receipt.gasUsed))
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
    "\nFunction Signature: "+self.input[:10] if (self.input!="0x00" and not self.contractAddress) else ""))
    
        if self.logs:
            print("  Events In This Transaction\n  ---------------------------")
        for event in self.logs:
            topic = TOPICS[event.topics[0].hex()]
            print("  "+topic[0])
            for i, (key, type_) in enumerate([i[:2] for i in topic[1] if i[2]], start=1):
                value = decode_single(type_, event.topics[i])
                if type(value) is bytes:
                    value = web3.toHex(value)
                print("    {}: {}".format(key, value))
            names = [i[0] for i in topic[1] if not i[2]]
            types = [i[1] if i[1]!="bytes" else "bytes[]" for i in topic[1] if not i[2]]
            decoded = decode_abi(types, HexBytes(event.data))
            for key, value in zip(names, decoded):
                if type(value) is bytes:
                    value = web3.toHex(value)
                print("    {}: {}".format(key, value))
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
    json_file = './build/contracts/{}.json'.format(name)
    data = COMPILED[name]
    data['networks'][str(int(time.time()))] = {
        'address': address,
        'transactionHash': txid,
        'network': CONFIG['active_network'],
        'owner': owner }
    json.dump(COMPILED[name], open(json_file, 'w'), sort_keys=True, indent=4)

def compile_contracts():
    for folder in ('./build', './build/contracts'):
        if not os.path.exists(folder):
            os.mkdir(folder)
    contract_files = ["{}/{}".format(i[0],x) for i in os.walk('contracts') for x in i[2]] 
    if not contract_files:
        sys.exit("ERROR: Cannot find any .sol files in contracts folder")
    print("Compiling contracts...\n Optimizer: {}".format("Enabled   Runs: {}".format(
            CONFIG['solc']['runs']) if CONFIG['solc']['optimize'] else "Disabled"))
    compiler_info = CONFIG['solc'].copy()
    compiler_info['version'] = solc.get_solc_version_string().strip('\n')
    final = {}
    for filename in contract_files:
        names = [[x.strip('\t') for x in i.split(' ') if x]
                 for i in open(filename).readlines()]
        for name in [i[1] for i in names if i[0] in ("contract", "library")]:
            json_file = './build/contracts/{}.json'.format(name)
            if os.path.exists(json_file):
                try:
                    compiled = json.load(open(json_file))
                    if (compiled['compiler'] == compiler_info and
                        compiled['updatedAt'] >= os.path.getmtime(filename)):
                        networks = dict(
                            (k,v) for k,v in compiled['networks'].items()
                            if 'persist' in CONFIG['networks'][v['network']] and 
                            CONFIG['networks'][v['network']]['persist'])
                        if networks != compiled['networks']:
                            compiled['networks'] = networks
                            json.dump(compiled, open(json_file, 'w'),
                                      sort_keys = True, indent = 4)
                        final[name] = compiled
                        continue
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
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
            print(" {}...".format(name))
            compiled = solc.compile_standard(
                input_json,
                optimize = CONFIG['solc']['optimize'],
                optimize_runs = CONFIG['solc']['runs'],
                allow_paths = ".")
            for name, data in compiled['contracts'][filename].items():
                json_file = './build/contracts/{}.json'.format(name)
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

def _topics():
    try:
        topics = json.load(open(BROWNIE_FOLDER+"/topics.json", 'r'))
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        topics = {}
    events = [x for i in COMPILED.values() for x in i['abi'] if x['type']=="event"]
    topics.update(dict((
        web3.sha3(text="{}({})".format(
            i['name'], ",".join(x['type'] for x in i['inputs']))).hex(),
        [i['name'], [(x['name'],x['type'],x['indexed']) for x in i['inputs']]]
        ) for i in events))
    json.dump(topics, open(BROWNIE_FOLDER+"/topics.json", 'w'))
    return topics


web3 = web3()
UNITS = {
    'kwei': 3, 'babbage': 3, 'mwei': 6, 'lovelace': 6, 'gwei': 9, 'shannon': 9,
    'microether': 12, 'szabo': 12, 'milliether': 15, 'finney': 15, 'ether': 18 }
compile_contracts()
TOPICS = _topics()
