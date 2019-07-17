#!/usr/bin/python3

import pytest

from brownie.network.account import Account
from brownie.network.contract import Contract
from brownie.network.event import EventDict
from brownie import accounts, Wei


def test_value():
    tx = accounts[0].transfer(accounts[1], "1 ether")
    assert type(tx.value) is Wei
    assert tx.value == 1000000000000000000


def test_sender_receiver():
    tx = accounts[0].transfer(accounts[1], "1 ether")
    assert type(tx.sender) is Account
    assert tx.sender == accounts[0]
    assert type(tx.receiver) is str
    assert tx.receiver == accounts[1].address


def test_receiver_contract(token):
    tx = token.transfer(accounts[1], 1000, {'from': accounts[0]})
    assert type(tx.receiver) is Contract
    assert tx.receiver == token
    data = token.balanceOf.encode_abi(accounts[0])
    tx = accounts[0].transfer(token.address, 0, data=data)
    assert type(tx.receiver) is Contract
    assert tx.receiver == token


def test_contract_address(token):
    tx = accounts[0].transfer(accounts[1], "1 ether")
    assert tx.contract_address is None
    assert type(token.tx.contract_address) is Contract
    assert token.tx.contract_address == token
    assert token.tx.receiver is None


def test_input(token):
    data = token.transfer.encode_abi(accounts[1], 1000)
    tx = token.transfer(accounts[1], 1000, {'from': accounts[0]})
    assert tx.input == data


def test_fn_name(token):
    tx = token.transfer(accounts[1], 1000, {'from': accounts[0]})
    assert tx.contract_name == "Token"
    assert tx.fn_name == "transfer"
    assert tx._full_name() == "Token.transfer"
    data = token.transfer.encode_abi(accounts[1], 1000)
    tx = accounts[0].transfer(token, 0, data=data)
    assert tx.contract_name == "Token"
    assert tx.fn_name == "transfer"
    assert tx._full_name() == "Token.transfer"


def test_return_value(token):
    balance = token.balanceOf(accounts[0])
    assert balance == token.balanceOf.transact(accounts[0]).return_value
    data = token.balanceOf.encode_abi(accounts[0])
    assert balance == accounts[0].transfer(token, 0, data=data).return_value


def test_modified_state(console_mode, token):
    assert token.tx.modified_state
    tx = token.transfer(accounts[1], 1000, {'from': accounts[0]})
    assert tx.status == 1
    assert tx.modified_state
    tx = token.transfer(accounts[1], 1000, {'from': accounts[2]})
    assert tx.status == 0
    assert not tx.modified_state
    tx = accounts[0].transfer(accounts[1], "1 ether")
    assert tx.status == 1
    assert not tx.modified_state


def test_revert_msg(console_mode, tester):
    tx = tester.testRevertStrings(0)
    assert tx.revert_msg == "zero"
    tx = tester.testRevertStrings(1)
    assert tx.revert_msg == "dev: one"
    tx = tester.testRevertStrings(2)
    assert tx.revert_msg == "two"
    tx = tester.testRevertStrings(3)
    assert tx.revert_msg == ""
    tx = tester.testRevertStrings(31337)
    assert tx.revert_msg == "dev: great job"


def test_events(console_mode, tester):
    tx = tester.testRevertStrings(5)
    assert tx.status == 1
    assert type(tx.events) is EventDict
    assert 'Debug' in tx.events
    tx = tester.testRevertStrings(0)
    assert tx.status == 0
    assert type(tx.events) is EventDict
    assert 'Debug' in tx.events


def test_hash(tester):
    a = tester.doNothing()
    b = tester.doNothing()
    hash(a)
    assert a != b
    assert a == a


def test_attribute_error(tester):
    tx = tester.doNothing()
    with pytest.raises(AttributeError):
        tx.unknownthing
