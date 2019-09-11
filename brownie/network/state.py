#!/usr/bin/python3

from typing import List, Dict, Iterable, Any
from .rpc import Rpc
from brownie.convert import to_address
from brownie._singleton import _Singleton

rpc = Rpc()


class TxHistory(metaclass=_Singleton):

    '''List-like singleton container that contains TransactionReceipt objects.
    Whenever a transaction is broadcast, the TransactionReceipt is automatically
    added to this container.'''

    def __init__(self) -> None:
        self._list: List = []
        self.gas_profile: Dict = {}
        rpc._revert_register(self)

    def __repr__(self) -> str:
        return str(self._list)

    def __bool__(self) -> bool:
        return bool(self._list)

    def __contains__(self, item: Any) -> bool:
        return item in self._list

    def __iter__(self) -> Iterable:
        return iter(self._list)

    def __getitem__(self, key: Any) -> Any:
        return self._list[key]

    def __len__(self) -> int:
        return len(self._list)

    def _reset(self) -> None:
        self._list.clear()

    def _revert(self, height: int) -> None:
        self._list = [i for i in self._list if i.block_number <= height]

    def _add_tx(self, tx: Any) -> None:
        self._list.append(tx)

    def clear(self) -> None:
        self._list.clear()

    def copy(self) -> List:
        '''Returns a shallow copy of the object as a list'''
        return self._list.copy()

    def from_sender(self, account: Any) -> List:
        '''Returns a list of transactions where the sender is account'''
        return [i for i in self._list if i.sender == account]

    def to_receiver(self, account: Any) -> List:
        '''Returns a list of transactions where the receiver is account'''
        return [i for i in self._list if i.receiver == account]

    def of_address(self, account: Any) -> List:
        '''Returns a list of transactions where account is the sender or receiver'''
        return [i for i in self._list if i.receiver == account or i.sender == account]

    def _gas(self, fn_name: str, gas_used: int) -> None:
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


_contract_map: Dict = {}


def find_contract(address: Any) -> Any:
    '''Given an address, returns the related Contract object.'''
    address = to_address(address)
    if address not in _contract_map:
        return None
    return _contract_map[address]


def get_current_dependencies() -> List:
    '''Returns a list of the currently deployed contracts and their dependencies.'''
    dependencies = set(v._name for v in _contract_map.values())
    for contract in _contract_map.values():
        dependencies.update(contract._build['dependencies'])
    return sorted(dependencies)


# _add_contract and _remove_contract are called by ContractContainer when Contract
#  objects are created or destroyed - don't call them directly or things will start
# to break in strange places!

def _add_contract(contract: Any) -> None:
    _contract_map[contract.address] = contract


def _remove_contract(contract: Any) -> None:
    del _contract_map[contract.address]
