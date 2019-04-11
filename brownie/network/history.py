#!/usr/bin/python3

from collections import OrderedDict

from eth_utils import to_checksum_address

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

    def find_contract(self, address):
        address = to_checksum_address(str(address))
        contracts = [x for v in self._contracts.values() for x in v.values()]
        return next((i for i in contracts if i == address), None)

    def get_contracts(self, name):
        if name not in self._contracts:
            self._contracts[name] = OrderedDict()
        return self._contracts[name]

    def copy(self):
        return self._tx.copy()


history = TxHistory()
