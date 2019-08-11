#!/usr/bin/python3

from copy import deepcopy
import pytest

from brownie import Wei
from brownie.network.contract import (
    Contract,
    ContractCall,
    ContractTx,
    OverloadedMethod,
)


@pytest.fixture
def build(testproject):
    build = testproject._build.get('BrownieTester')
    yield deepcopy(build)


def test_namespace_collision(accounts, build):
    build['abi'].append({
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
        Contract(None, build, str(accounts[1]), None)


def test_overloaded(accounts, build):
    build['abi'].append({
        'constant': False,
        'inputs': [
            {'name': '_to', 'type': 'address'},
            {'name': '_value', 'type': 'uint256'},
            {'name': '_test', 'type': 'uint256'}
        ],
        'name': 'revertStrings',
        'outputs': [{'name': '', 'type': 'bool'}],
        'payable': False,
        'stateMutability': 'nonpayable',
        'type': 'function'
    })
    c = Contract(None, build, str(accounts[1]), None)
    fn = c.revertStrings
    assert type(fn) == OverloadedMethod
    assert len(fn) == 2
    assert type(fn['uint']) == ContractTx
    assert fn['address', 'uint256', 'uint256'] == fn['address, uint256, uint256']
    assert fn['uint'] == fn['uint256']
    assert fn['uint'] != fn['address, uint256, uint256']
    repr(fn)


def test_set_methods(accounts, build):
    c = Contract(None, build, str(accounts[1]), None)
    for item in build['abi']:
        if item['type'] != "function":
            if 'name' not in item:
                continue
            assert not hasattr(c, item['name'])
        elif item['stateMutability'] in ('view', 'pure'):
            assert type(getattr(c, item['name'])) == ContractCall
        else:
            assert type(getattr(c, item['name'])) == ContractTx


def test_balance(accounts, build):
    balance = Contract(None, build, str(accounts[1]), None).balance()
    assert type(balance) is Wei
    assert balance == "100 ether"


def test_comparison(accounts, build):
    c = Contract(None, build, str(accounts[1]), None)
    assert c != 123
    assert c == str(accounts[1])
    assert c != Contract(None, build, str(accounts[2]), None)


def test_repr(accounts, build):
    c = Contract(None, build, str(accounts[1]), None)
    repr(c)
