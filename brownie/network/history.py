#!/usr/bin/python3

import sys

from .rpc import Rpc
from .web3 import Web3
from brownie.convert import to_address
from brownie._singleton import _Singleton

rpc = Rpc()
web3 = Web3()
rpc._revert_register(sys.modules[__name__])


class TxHistory(metaclass=_Singleton):

    '''List-like singleton container that contains TransactionReceipt objects.
    Whenever a transaction is broadcast, the TransactionReceipt is automatically
    added to this container.'''

    def __init__(self):
        self._list = []
        self.gas_profile = {}
        rpc._revert_register(self)

    def __repr__(self):
        return str(self._list)

    def __bool__(self):
        return bool(self._list)

    def __contains__(self, item):
        return item in self._list

    def __iter__(self):
        return iter(self._list)

    def __getitem__(self, key):
        return self._list[key]

    def __len__(self):
        return len(self._list)

    def _reset(self):
        self._list.clear()

    def _revert(self, height):
        self._list = [i for i in self._list if i.block_number <= height]

    def _add_tx(self, tx):
        self._list.append(tx)

    def clear(self):
        self._list.clear()

    def copy(self):
        '''Returns a shallow copy of the object as a list'''
        return self._list.copy()

    def from_sender(self, account):
        '''Returns a list of transactions where the sender is account'''
        return [i for i in self._list if i.sender == account]

    def to_receiver(self, account):
        '''Returns a list of transactions where the receiver is account'''
        return [i for i in self._list if i.receiver == account]

    def of_address(self, account):
        '''Returns a list of transactions where account is the sender or receiver'''
        return [i for i in self._list if i.receiver == account or i.sender == account]

    def _gas(self, fn_name, gas_used):
        if fn_name not in self.gas_profile:
            self.gas_profile[fn_name] = {
                'avg': gas_used,
                'high': gas_used,
                'low': gas_used,
                'count': 1
            }
            return
        gas = self.gas_profile[fn_name]
        gas.update({
            'avg': (gas['avg'] * gas['count'] + gas_used) // (gas['count'] + 1),
            'high': max(gas['high'], gas_used),
            'low': min(gas['low'], gas_used)
        })
        gas['count'] += 1


_contract_map = {}


def find_contract(address):
    '''Given an address, returns the related Contract object.'''
    address = to_address(address)
    if address not in _contract_map:
        return None
    return _contract_map[address]


def get_current_dependencies():
    '''Returns a list of the currently deployed contracts and their dependencies.'''
    dependencies = set(v._name for v in _contract_map.values())
    for contract in _contract_map.values():
        dependencies.update(contract._build['dependencies'])
    return sorted(dependencies)


# _add_contract and _remove_contract are called by ContractContainer when Contract
#  objects are created or destroyed - don't call them directly or things will start
# to break in strange places!

def _add_contract(contract):
    _contract_map[contract.address] = contract


def _remove_contract(contract):
    del _contract_map[contract.address]


# RPC registry methods

def _reset():
    for contract in _contract_map.values():
        contract._reverted = True
    _contract_map.clear()


def _revert(height):
    for address, contract in list(_contract_map.items()):
        if contract.tx and contract.tx.block_number <= height:
            continue
        if len(web3.eth.getCode(contract.address).hex()) > 4:
            continue
        _contract_map[address]._reverted = True
        del _contract_map[address]
