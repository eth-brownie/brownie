#!/usr/bin/python3

import eth_event
from hexbytes import HexBytes
import json
from subprocess import Popen, DEVNULL
import sys
import time
from web3 import Web3, HTTPProvider

from lib.components.compiler import compile_contracts
from lib.components import config
CONFIG = config.CONFIG


class VirtualMachineError(Exception):

    def __init__(self,e):
        msg = eval(str(e))['message']
        if len(msg.split('revert ',maxsplit=1))>1:
            self.revert_msg = msg.split('revert ')[1]
        else:
            self.revert_msg = None
        super().__init__(msg)


class web3:

    def __init__(self):
        self._rpc = None
        self._init = True

    def __del__(self):
        if self._rpc:
            self._rpc.terminate()

    def _run(self):
        if self._init or sys.argv[1] == "console":
            verbose = True
            self._init = False
        else:
            verbose = False
        if verbose:
            print("Using network '{}'".format(CONFIG['active_network']['name']))
        if self._rpc:
            if verbose:
                print("Resetting environment...")
            self._rpc.terminate()
        if 'test-rpc' in CONFIG['active_network']:
            if verbose:
                print("Running '{}'...".format(CONFIG['active_network']['test-rpc']))
            self._rpc = Popen(
                CONFIG['active_network']['test-rpc'].split(' '),
                stdout = DEVNULL,
                stdin = DEVNULL,
                stderr = DEVNULL
            )
        web3 = Web3(HTTPProvider(CONFIG['active_network']['host']))
        for i in range(20):
            if web3.isConnected():
                break
            if i == 19:
               raise ConnectionError("Could not connect to {}".format(CONFIG['active_network']['host']))
            time.sleep(0.2)
        for name, fn in [(i,getattr(web3,i)) for i in dir(web3) if i[0].islower()]:
            setattr(self, name, fn)


class TransactionReceipt:

    _gas_profiles = {}
    _txhistory = []
    
    def __init__(self, txid, silent=False, name=None):
        self.fn_name = name
        self._txhistory.append(self)
        while True:
            tx = web3.eth.getTransaction(txid)
            if tx: break
            time.sleep(0.5)
        if CONFIG['logging']['tx'] and not silent:
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
            self._gas_profiles.setdefault(name,{'avg':0,'high':0,'low':float('inf'),'count':0})
            gas = self._gas_profiles[name]
            gas['avg'] = (gas['avg']*gas['count']+receipt.gasUsed)/(gas['count']+1)
            gas['count']+=1
            gas['high'] = max(gas['high'],receipt.gasUsed)
            gas['low'] = min(gas['low'],receipt.gasUsed)
        self.gasLimit = self.gas
        del self.gas
        if silent:
            return
        if CONFIG['logging']['tx'] >= 2:
            self.info()
        elif CONFIG['logging']['tx']:
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
                data = eth_event.decode_event(event, TOPICS[event.topics[0].hex()])
                print("  "+data['name'])
                for i in data['data']:
                    print("    {0[name]}: {0[value]}".format(i))
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
    if type(value) is not str:
        return int(value)
    if value[:2] == "0x":
        return int(value, 16)
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


def _generate_topics():
    try:
        topics = json.load(open(CONFIG['folders']['brownie']+"/topics.json", 'r'))
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        topics = {}
    contracts = compile_contracts()
    events = [x for i in contracts.values() for x in i['abi'] if x['type']=="event"]
    topics.update(eth_event.get_event_abi(events))
    json.dump(
        topics, open(CONFIG['folders']['brownie']+"/topics.json", 'w'),
        sort_keys=True, indent=4
    )
    return topics


web3 = web3()
UNITS = {
    'kwei': 3, 'babbage': 3, 'mwei': 6, 'lovelace': 6, 'gwei': 9, 'shannon': 9,
    'microether': 12, 'szabo': 12, 'milliether': 15, 'finney': 15, 'ether': 18 }

TOPICS = _generate_topics()
