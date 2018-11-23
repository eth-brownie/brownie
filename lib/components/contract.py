#!/usr/bin/python3

from collections import OrderedDict
import sys

from lib.components.eth import web3, TransactionReceipt

class _ContractBase:

    def __init__(self, name, abi):
        self.abi = abi
        self.name = name
        self.topics = dict((
            i['name'], 
            web3.sha3(
                text="{}({})".format(i['name'],",".join(x['type'] for x in i['inputs']))
                ).hex()
        ) for i in abi if i['type']=="event")


class ContractDeployer(_ContractBase):

    def __init__(self, name, interface):
        self.tx = None
        self.bytecode = interface['bin']
        self._deployed = OrderedDict()
        super().__init__(name, interface['abi'])
    
    def __iter__(self):
        return iter(self._deployed.values())

    def __getitem__(self, i):
        return list(self._deployed.values())[i]

    def __len__(self):
        return len(self._deployed)

    def __repr__(self):
        return "<{} ContractDeployer object>".format(self.name)

    def list(self):
        return list(self._deployed)

    def deploy(self, account, *args):
        contract = web3.eth.contract(abi = self.abi, bytecode = self.bytecode)
        tx = account._contract_tx(contract.constructor, args, {})
        deployed = self.at(tx.contractAddress, account)
        deployed.tx = tx
        return deployed
    
    def at(self, address, owner = None):
        address = web3.toChecksumAddress(address)
        if address in self._deployed:
            return self._deployed[address]
        self._deployed[address] = Contract(address, self.name, self.abi, owner)
        return self._deployed[address]


class Contract(str,_ContractBase):

    def __new__(cls, address, *args):
        return super().__new__(cls, address)

    def __init__(self, address, name, abi, owner):
        super().__init__(name, abi)
        self._contract = web3.eth.contract(address = address, abi = abi)
        for i in [i for i in abi if i['type']=="function"]:
            fn = getattr(self._contract.functions,i['name'])
            if i['stateMutability'] in ('view','pure'):
                setattr(self, i['name'], ContractCall(fn, i, owner))
            else:
                setattr(self, i['name'], ContractTx(fn, i, owner))
        self.owner = owner
    
    def __repr__(self):
        return "<{0.name} Contract object '{0.address}'>".format(self)

    def __str__(self):
        return self.__repr__()

    def __getattr__(self, name):
        return getattr(self._contract, name)

    def balance(self):
        return web3.eth.getBalance(self._contract.address)

class _ContractMethod:

    def __init__(self, fn, abi, owner):
        self._fn = fn
        self._abi = abi
        self._owner = owner

class ContractTx(_ContractMethod):

    def __call__(self, *args):
        if args and type(args[-1]) is dict:
            args, tx = (args[:-1], args[-1])
            if 'from' not in tx:
                tx['from'] = self._owner
            if 'value' in tx and type(tx['value']) is float:
                tx['value'] = int(tx['value'])
        else:
            tx = {'from': self._owner}
        return tx['from']._contract_tx(self._fn, args, tx)

class ContractCall(_ContractMethod):

    def __call__(self, *args):
        result = self._fn(*args).call()
        if type(result) is not list:
            return web3.toHex(result) if type(result) is bytes else result
        return [(web3.toHex(i) if type(i) is bytes else i) for i in result]