#!/usr/bin/python3

import os
import solc
from subprocess import Popen, DEVNULL
import sys
from web3 import Web3, HTTPProvider

from lib.components.config import CONFIG


def _format_args(args):
    if type(args[-1]) is dict:
        return args[:-1], args[-1]
    return args, {'from': web3.eth.accounts[0]}

class Network:

    def __init__(self):
        pass

    def deploy(self, name, *args):
        args, tx = _format_args(args)
        interface = next(v for k,v in _compiled.items() if k.split(':')[-1] == name)
        contract = self.web3.eth.contract(
            abi = interface['abi'],
            bytecode = interface['bin']
        )
        txid = contract.constructor(*args).transact(tx)
        txreceipt = self.web3.eth.waitForTransactionReceipt(txid)
        setattr(self, name, Contract(txreceipt.contractAddress, interface['abi']))
        return getattr(self, name)

class Contract:

    def __init__(self, address, abi):
        self._contract = web3.eth.contract(address = address, abi = abi)
        self._abi = dict((
            i['name'],
            True if i['stateMutability'] in ['view','pure'] else False
            ) for i in abi if i['type']=="function")
    
    def __getattr__(self, name):
        if name not in self._abi:
            return getattr(self._contract, name)
        def _call(*args):
            result = getattr(self._contract.functions,name)(*args).call()
            if type(result) is not list:
                return web3.toHex(result) if type(result) is bytes else result
            return [(web3.toHex(i) if type(i) is bytes else i) for i in result]
        def _tx(*args):
            args, tx = _format_args(args)
            result = getattr(self._contract.functions,name)(*args).transact(tx)
            return web3.toHex(result)
        return _call if self._abi[name] else _tx

if '--network' in sys.argv:
    name = sys.argv[sys.argv.index('--network')+1]
    try:
        netconf = CONFIG['networks'][name]
    except KeyError:
        sys.exit("ERROR: Network '{}' is not defined in config.json".format(name))
else:
    netconf = CONFIG['networks']['development']

if 'test-rpc' in netconf:
    rpc = Popen(netconf['test-rpc'].split(' '), stdout = DEVNULL, stdin = DEVNULL)
else:
    rpc = None

print("Compiling contracts...")
_compiled = solc.compile_files(
    ["{}/{}".format(i[0],x) for i in os.walk('contracts') for x in i[2]],
    optimize = CONFIG['solc']['optimize']
)

web3 = Network.web3 = Web3(HTTPProvider(netconf['host']))
Network.accounts = Network.web3.eth.accounts