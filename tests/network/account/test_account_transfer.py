#!/usr/bin/python3

import pytest

from brownie import network, accounts, config, web3
from brownie.exceptions import VirtualMachineError
from brownie.network.transaction import TransactionReceipt


def test_to_string():
    '''Can send to a string'''
    tx = accounts[0].transfer("0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E", 10000)
    assert tx.receiver == "0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E"


def test_to_account():
    '''Can send to an Account object'''
    tx = accounts[0].transfer(accounts[1], 10000)
    assert str(tx.receiver) == accounts[1].address


def test_to_contract(token):
    '''Can send to a Contract object'''
    tx = accounts[0].transfer(token, 0, data="0x06fdde03")
    assert str(tx.receiver) == token.address


def test_returns_tx_on_success():
    '''returns a TransactionReceipt on success'''
    tx = accounts[0].transfer(accounts[1], 1000)
    assert type(tx) == TransactionReceipt


def test_raises_on_revert(token):
    '''raises on revert'''
    with pytest.raises(VirtualMachineError):
        accounts[0].transfer(token, 10000)


def test_broadcast_revert(token):
    config['active_network']['broadcast_reverting_tx'] = False
    count = accounts[0].nonce
    with pytest.raises(VirtualMachineError):
        accounts[0].transfer(token, 10000)
    assert accounts[0].nonce == count
    config['active_network']['broadcast_reverting_tx'] = True
    with pytest.raises(VirtualMachineError):
        accounts[0].transfer(token, 10000)
    assert accounts[0].nonce == count + 1


def test_returns_tx_on_revert_in_console(console_mode, token):
    '''returns a tx on revert in console'''
    tx = accounts[0].transfer(token, 10000)
    assert type(tx) == TransactionReceipt
    assert tx.status == 0


def test_nonce(clean_network):
    '''nonces increment properly'''
    assert accounts[1].nonce == 0
    accounts[1].transfer(accounts[2], 1000)
    assert accounts[2].nonce == 0
    assert accounts[1].nonce == 1


def test_balance_int():
    '''transfers use the correct balance'''
    balance = accounts[0].balance()
    assert web3.eth.getBalance(accounts[0].address) == balance
    accounts[1].transfer(accounts[0], 1000)
    assert accounts[0].balance() == balance + 1000
    network.rpc.reset()
    assert web3.eth.getBalance(accounts[0].address) == balance


def test_balance_wei():
    '''transfer balances are converted using wei'''
    balance = accounts[0].balance()
    assert web3.eth.getBalance(accounts[0].address) == balance
    accounts[1].transfer(accounts[0], "1 ether")
    assert accounts[0].balance() == balance + 1000000000000000000
    network.rpc.reset()
    assert web3.eth.getBalance(accounts[0].address) == balance


def test_gas_price_manual():
    '''gas price is set correctly when specified in the call'''
    balance = accounts[0].balance()
    tx = accounts[0].transfer(accounts[1], 0, gas_price=100)
    assert tx.gas_price == 100
    assert accounts[0].balance() == balance - (100*21000)


def test_gas_price_automatic():
    '''gas price is set correctly using web3.eth.gasPrice'''
    config['active_network']['gas_price'] = False
    balance = accounts[0].balance()
    tx = accounts[0].transfer(accounts[1], 0)
    assert tx.gas_price == web3.eth.gasPrice
    assert accounts[0].balance() == balance - (tx.gas_price*21000)


def test_gas_price_config():
    '''gas price is set correctly from the config'''
    config['active_network']['gas_price'] = 50
    balance = accounts[0].balance()
    tx = accounts[0].transfer(accounts[1], 0)
    assert tx.gas_price == 50
    assert accounts[0].balance() == balance - (50*21000)


def test_gas_limit_manual():
    '''gas limit is set correctly when specified in the call'''
    tx = accounts[0].transfer(accounts[1], 1000, gas_limit=100000)
    assert tx.gas_limit == 100000
    assert tx.gas_used == 21000


def test_gas_limit_automatic():
    '''gas limit is set correctly using web3.eth.estimateGas'''
    config['active_network']['gas_limit'] = False
    tx = accounts[0].transfer(accounts[1], 1000)
    assert tx.gas_limit == 21000


def test_gas_limit_config():
    '''gas limit is set correctly from the config'''
    config['active_network']['gas_limit'] = 50000
    tx = accounts[0].transfer(accounts[1], 1000)
    assert tx.gas_limit == 50000
    assert tx.gas_used == 21000
    config['active_network']['gas_limit'] = False


def test_data():
    '''transaction data is set correctly'''
    tx = accounts[0].transfer(accounts[1], 1000)
    assert tx.input == "0x"
    tx = accounts[0].transfer(accounts[1], 1000, data="0x1234")
    assert tx.input == "0x1234"
