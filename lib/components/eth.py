#!/usr/bin/python3

from hexbytes import HexBytes
from subprocess import Popen, DEVNULL
import sys
import time
from web3 import Web3, HTTPProvider

from lib.components.config import CONFIG


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

web3 = web3()

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
    "Events: {}\n".format(
        "\n".join(["{}"])
    ) if self.logs else ""
    ))

    def __repr__(self):
        return "<Transaction object '{}'>".format(self.hash)