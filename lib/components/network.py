#!/usr/bin/python3

import os
import solc
from subprocess import Popen, DEVNULL
import sys
from web3 import Web3, HTTPProvider

from lib.components.config import CONFIG


class RPC(Popen):

    def __init__(self, cmd):
        super().__init__(cmd.split(' '), stdout = DEVNULL, stdin = DEVNULL)
    
    def __del__(self):
        self.terminate()

class Network:

    def __init__(self):
        pass

    def __getattr__(self,name):
        return getattr(web3,name)

    def deploy(self, name, *args):
        if type(args[-1]) is dict:
            args, tx = (args[:-1], args[-1])
        else:
            tx = {'from': web3.eth.accounts[0]}
        interface = next(v for k,v in compiled.items() if k.split(':')[-1] == name)
        contract = self.web3.eth.contract(
            abi = interface['abi'],
            bytecode = interface['bin']
        )
        txid = contract.constructor(*args).transact(tx)
        txreceipt = self.web3.eth.waitForTransactionReceipt(txid)
        contract = Contract(
            txreceipt.contractAddress,
            interface['abi'],
            tx['from']
        )
        if not hasattr(self, name):
            setattr(self, name, contract)
        else:
            i = next(i for i in range(1,10000) if not hasattr(self, name+str(i)))
            setattr(self, name+str(i), contract)
        return contract

class Contract:

    def __init__(self, address, abi, owner):
        self._contract = web3.eth.contract(address = address, abi = abi)
        self.abi = dict((
            i['name'],
            True if i['stateMutability'] in ['view','pure'] else False
            ) for i in abi if i['type']=="function")
        self.owner = owner
    
    def __getattr__(self, name):
        if name not in self.abi:
            return getattr(self._contract, name)
        def _call(*args):
            result = getattr(self._contract.functions,name)(*args).call()
            if type(result) is not list:
                return web3.toHex(result) if type(result) is bytes else result
            return [(web3.toHex(i) if type(i) is bytes else i) for i in result]
        def _tx(*args):
            if type(args[-1]) is dict:
                args, tx = (args[:-1], args[-1])
            else:
                tx = {'from': self.owner}
            result = getattr(self._contract.functions,name)(*args).transact(tx)
            return web3.toHex(result)
        return _call if self.abi[name] else _tx

    def revert(self,name,*args):
        if name not in self.abi:
            raise AttributeError("{} is not a valid function.".format(name))
        try:
            self.__getattr__(name)(*args)
            return False
        except ValueError:
            return True

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
if 'test-rpc' in netconf:
    rpc = RPC(netconf['test-rpc'])

contract_files = ["{}/{}".format(i[0],x) for i in os.walk('contracts') for x in i[2]] 
if not contract_files:
    sys.exit("ERROR: Cannot find any .sol files in contracts folder")
print("Compiling contracts...")
compiled = solc.compile_files(contract_files, optimize=CONFIG['solc']['optimize'])

web3 = Network.web3 = Web3(HTTPProvider(netconf['host']))
Network.accounts = Network.web3.eth.accounts