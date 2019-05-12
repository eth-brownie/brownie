#!/usr/bin/python3

from collections import OrderedDict

from .rpc import Rpc
from brownie.types.types import _Singleton
from brownie.types.convert import to_address
from .web3 import Web3

web3 = Web3()


class TxHistory(metaclass=_Singleton):

    '''List-like singleton container that contains TransactionReceipt objects.
    Whenever a transaction is broadcast, the TransactionReceipt is automatically
    added to this container.'''

    def __init__(self):
        self._list = []
        self._revert_lock = False
        Rpc()._objects.append(self)

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

    def _revert(self):
        if self._revert_lock:
            return
        height = web3.eth.blockNumber
        self._list = [i for i in self._list if i.block_number <= height]

    def _console_repr(self):
        return str(self._list)

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


class _ContractHistory(metaclass=_Singleton):

    '''Internal singleton dict of OrderedDicts that acts as a single container
    for ContractContainer lists.'''

    def __init__(self):
        self._dict = {}
        Rpc()._objects.append(self)

    def _reset(self):
        self._dict.clear()

    def _revert(self):
        height = web3.eth.blockNumber
        for name, contracts in self._dict.items():
            for contract in list(contracts.values()):
                if contract.tx and contract.tx.block_number <= height:
                    continue
                elif len(web3.eth.getCode(contract.address).hex()) > 4:
                    continue
                del self._dict[name][contract.address]

    def add(self, contract):
        name = contract._name
        self._dict.setdefault(name, OrderedDict())[contract.address] = contract

    def remove(self, contract):
        name = contract._name
        del self._dict[name][contract.address]

    def list(self, name):
        self._dict.setdefault(name, OrderedDict())
        return list(self._dict[name].values())

    def find(self, address):
        address = to_address(address)
        contracts = [x for v in self._dict.values() for x in v.values()]
        return next((i for i in contracts if i == address), None)
