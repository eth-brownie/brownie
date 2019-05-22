#!/usr/bin/python3

from copy import deepcopy
import pytest

from brownie import network
from brownie.project.build import Build
from brownie.network.contract import Contract, ContractCall, ContractTx

accounts = network.accounts
build = Build()


def test_namespace_collision():
    b = deepcopy(build['Token'])
    b['abi'].append({
        'constant': False,
        'inputs': [
            {'name': '_to', 'type': 'address'},
            {'name': '_value', 'type': 'uint256'},
            {'name': '_test', 'type': 'uint256'}
        ],
        'name': 'bytecode',
        'outputs': [{'name': '', 'type': 'bool'}],
        'payable': False,
        'stateMutability': 'nonpayable',
        'type': 'function'
    })
    with pytest.raises(AttributeError):
        Contract(str(accounts[1]), b, None)


def test_set_methods():
    c = Contract(str(accounts[1]), build['Token'], None)
    for item in build['Token']['abi']:
        if item['type'] != "function":
            if 'name' not in item:
                continue
            assert not hasattr(c, item['name'])
        elif item['stateMutability'] in ('view', 'pure'):
            assert type(getattr(c, item['name'])) == ContractCall
        else:
            assert type(getattr(c, item['name'])) == ContractTx


def test_balance():
    c = Contract(str(accounts[1]), build['Token'], None)
    assert c.balance() == 100000000000000000000
