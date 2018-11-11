#!/usr/bin/python3

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
        if '--network' in sys.argv:
            name = sys.argv[sys.argv.index('--network')+1]
            try:
                netconf = CONFIG['networks'][name]
                print("Using network '{}'".format(name))
            except KeyError:
                sys.exit("ERROR: Network '{}' is not defined in config.json".format(name))
        else:
            netconf = CONFIG['networks']['development']
            print("Using network 'development'")
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
            time.sleep(0.1)
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
        for k,v in tx.items():
            if type(v) is HexBytes:
                v = web3.toHex(v)
            setattr(self, k, v)
        if not tx.blockNumber:
            print("Transaction sent: {}".format(web3.toHex(txid)))
            print ("Waiting for confirmation...")
        receipt = web3.eth.waitForTransactionReceipt(txid)
        for k,v in [(k,v) for k,v in receipt.items() if k not in tx]:
            if type(v) is HexBytes:
                v = web3.toHex(v)
            setattr(self, k, v)
        print("""
Transaction was Mined
---------------------
Tx Hash: {0.hash}{2}
Block: {0.blockNumber}
Gas Used: {0.gasUsed}{1}
{3}""".format(
    self, "\nContract Deployed at: "+self.contractAddress if self.contractAddress else "",
    "\nInput: "+self.input if not self.contractAddress else "",
    #[i['topics'] for i in self.logs]
    "Events:\n{}\n".format(
        "\n\n".join(["{}\n{}".format(TOPICS[web3.toHex(i['topics'][0])], i) for i in self.logs])
    ) if self.logs else ""
    ))

    def __repr__(self):
        return "<Transaction object '{}'>".format(self.hash)
    

web3 = web3()

contract_files = ["{}/{}".format(i[0],x) for i in os.walk('contracts') for x in i[2]] 
if not contract_files:
    sys.exit("ERROR: Cannot find any .sol files in contracts folder")
print("Compiling contracts...")
COMPILED = solc.compile_files(contract_files, optimize=CONFIG['solc']['optimize'])

try:
    TOPICS = json.load(open(BROWNIE_FOLDER+"/topics.json", 'r'))
except (FileNotFoundError, json.decoder.JSONDecodeError):
    TOPICS = {}

events = [x for i in COMPILED.values() for x in i['abi'] if x['type']=="event"]
TOPICS.update(dict((
    web3.toHex(web3.sha3(text="{}({})".format(i['name'],",".join(x['type'] for x in i['inputs'])))),
    [i['name'], [(x['name'],x['type'],x['indexed']) for x in i['inputs']]]
    ) for i in events))

json.dump(TOPICS, open(BROWNIE_FOLDER+"/topics.json", 'w'))