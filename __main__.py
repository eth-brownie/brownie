#!/usr/bin/python3

import importlib
import json
import os
import solc
from subprocess import Popen, DEVNULL
import sys
from web3 import Web3, HTTPProvider

sys.path.insert(0,"")

CONFIG = json.load(open(__file__.rsplit('/',maxsplit = 1)[0]+'/config.json', 'r'))

conf_path = os.path.abspath('.')+"/tests/config.json"
if os.path.exists(conf_path):
    for k,v in json.load(open(conf_path, 'r')).items():
        if type(v) is dict and k in CONFIG:
            CONFIG[k].update(v)
        else: CONFIG[k] = v

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
web3 = Web3(HTTPProvider(netconf['host']))
accounts = web3.eth.accounts

print("Compiling contracts...")
_compiled = solc.compile_files(
    ["{}/{}".format(i[0],x) for i in os.walk('contracts') for x in i[2]],
    optimize = CONFIG['solc']['optimize']
)

class Contracts:

    def __init__(self):
        pass

    def deploy(self, name, *args, **kwargs):
        if not kwargs:
            kwargs = {'from': accounts[0]}
        interface = next(v for k,v in _compiled.items() if k.split(':')[-1] == name)
        contract = web3.eth.contract(
            abi = interface['abi'],
            bytecode = interface['bin']
        )
        txid = contract.constructor(*args).transact(kwargs)
        txreceipt = web3.eth.waitForTransactionReceipt(txid)
        setattr(self, name, web3.eth.contract(
            address = txreceipt.contractAddress,
            abi = interface['abi']
        ))
        return getattr(self, name)


def deploy_contract(name, *args, **kwargs):
    if not kwargs:
        kwargs = {'from': accounts[0]}
    interface = next(v for k,v in _compiled.items() if k.split(':')[-1] == name)
    contract = web3.eth.contract(
        abi = interface['abi'],
        bytecode = interface['bin']
    )
    txid = contract.constructor(*args).transact(kwargs)
    txreceipt = web3.eth.waitForTransactionReceipt(txid)
    return web3.eth.contract(
        address = txreceipt.contractAddress,
        abi = interface['abi']
    )

if not os.path.exists('tests'):
    os.mkdir('tests')
    open('tests/__init__.py','a')
    sys.exit("ERROR: There are no test files to run.")

if len(sys.argv)>1 and sys.argv[1][:2]!="--":
    if not os.path.exists('tests/{}.py'.format(sys.argv[1])):
        sys.exit("ERROR: Cannot find tests/{}.py".format(sys.argv[1]))
    test_files = [sys.argv[1]]
else:
    test_files = [i[:-3] for i in os.listdir('tests') if i[-3:] == ".py"]
    test_files.remove('__init__')

if os.path.exists('tests/{}.py'.format(CONFIG['setup'])):
    setup_module = importlib.import_module("tests.{}".format(CONFIG['setup']))
    if not hasattr(setup_module, 'setup'):
        sys.exit("ERROR: Setup module has no setup() function defined.")
    print("Imported setup module from tests/{}.py".format(CONFIG['setup']))
    test_files.remove(CONFIG['setup'])
else:
    setup_module = False
    print("WARNING: No setup module found.")

for name in test_files:
    print("Running {}...".format(name))
    contracts = Contracts()
    if setup_module:
        setup_module.setup(contracts, accounts, web3)
    module = importlib.import_module("tests."+name)
    if not hasattr(module, 'test'):
        print("WARNING: Test module '{}' has no test() function defined.")
        continue
    module.test(contracts, accounts, web3)