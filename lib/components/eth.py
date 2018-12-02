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


class web3:

    _rpc = None
    
    def __init__(self):
        name = CONFIG['default_network']
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
            print("Transaction confirmed: block {}  gas spent {}".format(
                tx.blockNumber, tx.gasUsed))
    
    
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
            decoded = decode_abi([i[1] if i[1]!="bytes" else "bytes[]" for i in topic[1] if not i[2]], HexBytes(event.data))
            for key, value in zip(names, decoded):
                if type(value) is bytes:
                    value = web3.toHex(value)
                print("    {}: {}".format(key, value))
        print()

    def __repr__(self):
        return "<Transaction object '{}'>".format(self.hash)
    

web3 = web3()

contract_files = ["{}/{}".format(i[0],x) for i in os.walk('contracts') for x in i[2]] 
if not contract_files:
    sys.exit("ERROR: Cannot find any .sol files in contracts folder")
print("Compiling contracts...\n Optimizer: {}".format("Enabled   Runs: {}".format(
        CONFIG['solc']['runs']) if CONFIG['solc']['optimize'] else "Disabled"))
COMPILED = solc.compile_files(
    contract_files,
    optimize = CONFIG['solc']['optimize'],
    optimize_runs = CONFIG['solc']['runs'])

names = [i.split(':')[1] for i in COMPILED.keys()]
duplicates = set(i for i in names if names.count(i)>1)
if duplicates:
    raise ValueError("Multiple contracts with the same name: {}".format(name, ",".join(duplicates)))

try:
    TOPICS = json.load(open(BROWNIE_FOLDER+"/topics.json", 'r'))
except (FileNotFoundError, json.decoder.JSONDecodeError):
    TOPICS = {}

events = [x for i in COMPILED.values() for x in i['abi'] if x['type']=="event"]
TOPICS.update(dict((
    web3.sha3(text="{}({})".format(i['name'],",".join(x['type'] for x in i['inputs']))).hex(),
    [i['name'], [(x['name'],x['type'],x['indexed']) for x in i['inputs']]]
    ) for i in events))

json.dump(TOPICS, open(BROWNIE_FOLDER+"/topics.json", 'w'))