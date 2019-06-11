#!/usr/bin/python3

from copy import deepcopy
import pytest


from brownie import network, project
from brownie.project import build
from brownie.network.contract import ContractContainer
from brownie.exceptions import AmbiguousMethods

accounts = network.accounts


def test_ambiguous_methods():
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
    with pytest.raises(AmbiguousMethods):
        ContractContainer(b)


def test_get_method():
    assert project.Token.get_method(
        "0xa9059cbb0000000000000000000000000a4a71b2518f7a3273595cba15c3308182b32cd1"
        "0000000000000000000000000000000000000000000000020f5b1eaad8d80000"
    ) == "transfer"


def test_container(clean_network):
    Token = project.Token
    assert len(Token) == 0
    t = Token.deploy("", "", 0, 0, {'from': accounts[0]})
    t2 = Token.deploy("", "", 0, 0, {'from': accounts[0]})
    assert len(Token) == 2
    assert Token[0] == t
    assert Token[1] == t2
    assert list(Token) == [t, t2]
    assert t in Token
    del Token[0]
    assert len(Token) == 1
    assert Token[0] == t2
    network.rpc.reset()
    assert len(Token) == 0


def test_remove_at(clean_network):
    Token = project.Token
    t = Token.deploy("", "", 0, 0, {'from': accounts[0]})
    Token.remove(t)
    assert len(Token) == 0
    assert Token.at(t.address) == t
    assert len(Token) == 1
