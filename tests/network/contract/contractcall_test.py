#!/usr/bin/python3

from brownie import network, project, history
from brownie._config import ARGV

accounts = network.accounts
web3 = network.web3

abi = {
    'constant': True,
    'inputs': [],
    'name': 'totalSupply',
    'outputs': [{'name': '', 'type': 'uint256'}],
    'payable': False,
    'stateMutability': 'view',
    'type': 'function'
}


def test_attributes():
    token = project.Token.deploy("", "", 18, 1000000, {'from': accounts[0]})
    assert token.totalSupply._address == token.address
    assert token.totalSupply._name == "Token.totalSupply"
    assert token.totalSupply._owner == accounts[0]
    assert token.totalSupply.abi == abi
    assert token.totalSupply.signature == "0x18160ddd"


def test_encode_abi():
    data = project.Token[0].balanceOf.encode_abi("0x2f084926Fd8A120089cA5F622975Fe7F1306AFF9")
    assert data == "0x70a082310000000000000000000000002f084926fd8a120089ca5f622975fe7f1306aff9"


def test_transact():
    nonce = accounts[0].nonce
    tx = project.Token[0].balanceOf.transact(accounts[0], {'from': accounts[0]})
    assert tx.return_value == project.Token[0].balanceOf(accounts[0])
    assert accounts[0].nonce == nonce + 1


def test_always_transact():
    balance = project.Token[0].balanceOf(accounts[0])
    ARGV['always_transact'] = True
    try:
        height = web3.eth.blockNumber
        result = project.Token[0].balanceOf(accounts[0])
        tx = history[-1]
        assert balance == result
        assert web3.eth.blockNumber == height + 1
        assert tx.fn_name == "Token.balanceOf"
    finally:
        ARGV['always_transact'] = False
