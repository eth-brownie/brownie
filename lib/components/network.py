#!/usr/bin/python3

import os
import solc
from subprocess import Popen, DEVNULL
import sys
from web3 import Web3, HTTPProvider

from lib.components.config import CONFIG

class Network:

    def __init__(self):
        pass

    def deploy(self, name, *args, **kwargs):
        if not kwargs:
            kwargs = {'from': self.accounts[0]}
        interface = next(v for k,v in _compiled.items() if k.split(':')[-1] == name)
        contract = self.web3.eth.contract(
            abi = interface['abi'],
            bytecode = interface['bin']
        )
        txid = contract.constructor(*args).transact(kwargs)
        txreceipt = self.web3.eth.waitForTransactionReceipt(txid)
        setattr(self, name, self.web3.eth.contract(
            address = txreceipt.contractAddress,
            abi = interface['abi']
        ))
        return getattr(self, name)


print("Compiling contracts...")
_compiled = solc.compile_files(
    ["{}/{}".format(i[0],x) for i in os.walk('contracts') for x in i[2]],
    optimize = CONFIG['solc']['optimize']
)

if '--network' in sys.argv:
    name = sys.argv[sys.argv.index('--network')+1]
    try:
        netconf = CONFIG['networks'][name]
    except KeyError:
        sys.exit("ERROR: Network '{}' is not defined in config.json".format(name))
else:
    netconf = CONFIG['networks']['development']

if 'test-rpc' in netconf:
    rpc = Popen(netconf['test-rpc'], stdout = DEVNULL, stdin = DEVNULL)
Network.web3 = Web3(HTTPProvider(netconf['host']))
Network.accounts = Network.web3.eth.accounts