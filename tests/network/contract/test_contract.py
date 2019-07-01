#!/usr/bin/python3

from copy import deepcopy
import pytest

from brownie import accounts
from brownie.project import build
from brownie.network.contract import Contract, ContractCall, ContractTx, OverloadedMethod


def test_namespace_collision():
    b = deepcopy(build.get('Token'))
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


def test_overloaded():
    b = deepcopy(build.get('Token'))
    b['abi'].append({
        'constant': False,
        'inputs': [
            {'name': '_to', 'type': 'address'},
            {'name': '_value', 'type': 'uint256'},
            {'name': '_test', 'type': 'uint256'}
        ],
        'name': 'transfer',
        'outputs': [{'name': '', 'type': 'bool'}],
        'payable': False,
        'stateMutability': 'nonpayable',
        'type': 'function'
    })
    c = Contract(str(accounts[1]), b, None)
    fn = c.transfer
    assert type(fn) == OverloadedMethod
    assert len(fn) == 2
    assert type(fn['address', 'uint']) == ContractTx
    assert fn['address, uint256'] != fn['address, uint256, uint256']
    assert fn['address', 'uint'] == fn['address,uint256']


def test_set_methods():
    c = Contract(str(accounts[1]), build.get('Token'), None)
    for item in build.get('Token')['abi']:
        if item['type'] != "function":
            if 'name' not in item:
                continue
            assert not hasattr(c, item['name'])
        elif item['stateMutability'] in ('view', 'pure'):
            assert type(getattr(c, item['name'])) == ContractCall
        else:
            assert type(getattr(c, item['name'])) == ContractTx


def test_balance():
    c = Contract(str(accounts[1]), build.get('Token'), None)
    assert c.balance() == 100000000000000000000


def test_comparison():
    c = Contract(str(accounts[1]), build.get('Token'), None)
    assert c != 123
    assert c == str(accounts[1])
    assert c != Contract(str(accounts[2]), build.get('Token'), None)


def test_repr():
    c = Contract(str(accounts[1]), build.get('Token'), None)
    repr(c)
