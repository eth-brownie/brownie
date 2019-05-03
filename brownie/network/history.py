#!/usr/bin/python3

from collections import OrderedDict

from brownie.types.convert import to_address
from brownie.network.web3 import web3
import brownie._registry as _registry


class TxHistory:

    def __init__(self):
        self._contracts = {}
        self._tx = []
        _registry.add(self)

    def __contains__(self, other):
        return other in self._tx

    def __iter__(self):
        return iter(self._tx)

    def __getitem__(self, item):
        return self._tx[item]

    def __len__(self):
        return len(self._tx)

    def _console_repr(self):
        return str(self._tx)

    def _notify_reset(self):
        self._tx.clear()
        self._contracts.clear()

    def _notify_revert(self):
        height = web3.eth.blockNumber
        self._tx = [i for i in self._tx if i.block_number <= height]
        for name, contracts in self._contracts.items():
            keep = []
            for contract in contracts.values():
                if contract.tx:
                    if contract.tx.block_number <= height:
                        keep.append(contract)
                elif len(web3.eth.getCode(contract._contract.address).hex()) > 4:
                    keep.append(contract)
            self._contracts[name] = OrderedDict((i._contract.address, i) for i in keep)

    def _add_tx(self, tx):
        self._tx.append(tx)

    def to_address(self, account):
        return [i for i in self._tx if i.receiver == account]

    def from_address(self, account):
        return [i for i in self._tx if i.sender == account]

    def of(self, account):
        return [i for i in self._tx if i.receiver == account or i.sender == account]

    def copy(self):
        return self._tx.copy()


class _ContractHistory:

    def __init__(self):
        self._contracts = {}

    def add(self, contract):
        name = contract._name
        self._contracts.setdefault(name, OrderedDict())[contract.address] = contract

    def remove(self, contract):
        name = contract._name
        del self._contracts[name][contract.address]

    def list(self, name):
        self._contracts.setdefault(name, OrderedDict())
        return list(self._contracts[name].values())

    def find(self, address):
        address = to_address(address)
        contracts = [x for v in self._contracts.values() for x in v.values()]
        return next((i for i in contracts if i == address), None)


history = TxHistory()
_contracts = _ContractHistory()