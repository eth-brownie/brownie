#!/usr/bin/python3

from collections import OrderedDict
import importlib
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

    def __init__(self, module):
        self._module = module
        self.accounts = [Account(i) for i in web3.eth.accounts]
        for name, interface in compiled.items():
            setattr(self, name.split(':')[-1], ContractDeployer(interface))
        self._exposed = dict(
            [(i,getattr(self,i)) for i in dir(self) if i[0]!='_'] +
            [(i,getattr(web3,i)) for i in dir(web3) if i[0].islower()])
        module.__dict__.update(self._exposed)
        if hasattr(module, 'DEPLOYMENT'):
            self.run(module.DEPLOYMENT)
    
    def add_account(self, priv_key):
        w3account = web3.eth.account.privateKeyToAccount(priv_key)
        account = LocalAccount(w3account.address)
        account._acct = w3account
        account._priv_key = priv_key
        self.accounts.append(account)
        return account

    def run(self, name):
        module = importlib.import_module("deployments."+name)
        module.__dict__.update(self._exposed)
        print("Running deployment script '{}'...".format(name))
        try:
            module.deploy()
            print("Deployment of '{}' was successful.".format(name))
        except Exception as e:
            print("ERROR: Deployment of '{}' failed due to {} - {}".format(
                    name, type(e).__name__, e))

    def reset(self):
        Network(self._module)
        print("Environment has been reset.")
        # todo - make this reset the RPC as well





class _ContractBase:

    def __init__(self, abi):
        self.abi = abi
        self.topics = dict((
            i['name'],web3.toHex(web3.sha3(text="{}({})".format(i['name'],",".join(x['type'] for x in i['inputs']))))
        ) for i in abi if i['type']=="event")

class ContractDeployer(_ContractBase):

    def __init__(self, interface):
        self.bytecode = interface['bin']
        self._deployed = OrderedDict()
        super().__init__(interface['abi'])
    
    def deploy(self, account, *args):
        contract = web3.eth.contract(abi = self.abi, bytecode = self.bytecode)
        txreceipt = account._contract_call(contract.constructor, args, {})
        if '--gas' in sys.argv:
            print("deploy {}: {} gas".format(name, txreceipt['gasUsed']))
        return self.at(txreceipt['contractAddress'], account)
    
    def at(self, address, owner = None):
        address = web3.toChecksumAddress(address)
        if address in self._deployed:
            return self._deployed[address]
        self._deployed[address] = Contract(address, self.abi, owner)
        return self._deployed[address]
    
    def addresses(self):
        return list(self._deployed)

    def __iter__(self):
        return iter(self._deployed.values())

    def __getitem__(self, i):
        return list(self._deployed.values())[i]


class Contract(_ContractBase):

    def __init__(self, address, abi, owner):
        super().__init__(abi)
        self._contract = web3.eth.contract(address = address, abi = abi)
        self._fn_map = dict((
            i['name'],
            True if i['stateMutability'] in ['view','pure'] else False
            ) for i in abi if i['type']=="function")
        self.owner = owner
    
    def __repr__(self):
        return "<Contract object '{}'>".format(self.address)

    def __getattr__(self, name):
        if name not in self._fn_map:
            return getattr(self._contract, name)
        def _call(*args):
            result = getattr(self._contract.functions,name)(*args).call()
            if type(result) is not list:
                return web3.toHex(result) if type(result) is bytes else result
            return [(web3.toHex(i) if type(i) is bytes else i) for i in result]
        def _tx(*args):
            if args and type(args[-1]) is dict:
                args, tx = (args[:-1], args[-1])
                if 'from' not in tx:
                    tx['from'] = self.owner
                if 'value' in tx and type(tx['value']) is float:
                    tx['value'] = int(tx['value'])
            else:
                tx = {'from': self.owner}
            fn = getattr(self._contract.functions,name)
            txreceipt = tx['from']._contract_call(fn, args, tx)
            if '--gas' in sys.argv:
                print("{}: {} gas".format(name, txreceipt['gasUsed']))
            return web3.toHex(txreceipt['transactionHash'])
        return _call if self._fn_map[name] else _tx

    def revert(self, name, *args):
        if name not in self._fn_map:
            raise AttributeError("{} is not a valid function.".format(name))
        try:
            self.__getattr__(name)(*args)
            return False
        except ValueError:
            return True

    def balance(self):
        return web3.eth.getBalance(self._contract.address)

class _AccountBase(str):

    def __init__(self, addr):
        self.address = addr
        self.nonce = web3.eth.getTransactionCount(self.address)

    def __repr__(self):
        return "<Account object '{}'>".format(self.address)

    def __str__(self):
        return self.address

    def balance(self):
        return web3.eth.getBalance(self.address)

    def deploy(self, contract, *args):
        return contract.deploy(self, *args)

    def revert(self, cmd, *args):
        if cmd not in ['transfer', 'deploy']:
            raise AttributeError("Unknown command")
        try:
            getattr(self, cmd)(*args)
            return False
        except ValueError:
            return True
    
    def estimate_gas(self, to, amount, data=""):
        return web3.eth.estimateGas({
            'from':self.address,
            'to':to,
            'data':data,
            'value':int(amount)
            })


class Account(_AccountBase):

    def transfer(self, to, amount, gas_price=None):
        txid = web3.eth.sendTransaction({
            'from': self.address,
            'to': to,
            'value': int(amount),
            'gasPrice': gas_price or web3.eth.gasPrice,
            'gas': self.estimate_gas(to, amount)
            })
        self.nonce += 1
        return web3.toHex(txid)

    def _contract_call(self, fn, args, tx):
        tx['from'] = self.address
        txid = fn(*args).transact(tx)
        self.nonce += 1
        return web3.eth.waitForTransactionReceipt(txid)

class LocalAccount(_AccountBase):

    def transfer(self, to, amount, gas_price=None):
        signed_tx = self._acct.signTransaction({
            'from': self.address,
            'nonce': self.nonce,
            'gasPrice': gas_price or web3.eth.gasPrice,
            'gas': self.estimate_gas(to, amount),
            'to': to,
            'value': int(amount),
            'data': ""
            }).rawTransaction
        txid = web3.eth.sendRawTransaction(signed_tx)
        self.nonce += 1
        return web3.toHex(txid)

    def _contract_call(self, fn, args, tx):
        tx.update({
            'from':self.address,
            'nonce':self.nonce,
            'gasPrice': web3.eth.gasPrice,
            'gas': fn(*args).estimateGas({'from': self.address}),
            })
        raw = fn(*args).buildTransaction(tx)
        txid = web3.eth.sendRawTransaction(
            self._acct.signTransaction(raw).rawTransaction)
        self.nonce += 1
        return web3.eth.waitForTransactionReceipt(txid)

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

web3 = Web3(HTTPProvider(netconf['host']))