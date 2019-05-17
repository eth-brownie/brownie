#!/usr/bin/python3

from brownie import network, config

accounts = network.accounts
web3 = network.web3


def test_address():
    '''addresses are set from web3.eth.address'''
    assert web3.eth.accounts[0] == accounts[0].address


def test_estimate_gas():
    '''gas limit is estimated correctly'''
    assert accounts[0].estimate_gas(accounts[1], 1000) == 21000
    limit = accounts[0].estimate_gas(accounts[1], 1000, data="0x1234")
    assert limit == accounts[0].transfer(accounts[1], 1000, data="0x1234").gas_used


def test_transfer_nonce():
    '''nonces increment properly'''
    assert accounts[1].nonce == 0
    accounts[1].transfer(accounts[2], 1000)
    assert accounts[2].nonce == 0
    assert accounts[1].nonce == 1
    network.rpc.reset()
    assert accounts[1].nonce == 0


def test_transfer_balance_int():
    '''transfers use the correct balance'''
    balance = accounts[0].balance()
    assert web3.eth.getBalance(accounts[0].address) == balance
    accounts[1].transfer(accounts[0], 1000)
    assert accounts[0].balance() == balance + 1000
    network.rpc.reset()
    assert web3.eth.getBalance(accounts[0].address) == balance


def test_transfer_balance_wei():
    '''transfer balances are converted using wei'''
    balance = accounts[0].balance()
    assert web3.eth.getBalance(accounts[0].address) == balance
    accounts[1].transfer(accounts[0], "1 ether")
    assert accounts[0].balance() == balance + 1000000000000000000
    network.rpc.reset()
    assert web3.eth.getBalance(accounts[0].address) == balance


def test_transfer_gas_price_manual():
    '''gas price is set correctly when specified in the call'''
    balance = accounts[0].balance()
    tx = accounts[0].transfer(accounts[1], 0, gas_price=100)
    assert tx.gas_price == 100
    assert accounts[0].balance() == balance - (100*21000)


def test_transfer_gas_price_automatic():
    '''gas price is set correctly using web3.eth.gasPrice'''
    config['active_network']['gas_price'] = False
    balance = accounts[0].balance()
    tx = accounts[0].transfer(accounts[1], 0)
    assert tx.gas_price == web3.eth.gasPrice
    assert accounts[0].balance() == balance - (tx.gas_price*21000)


def test_transfer_gas_price_config():
    '''gas price is set correctly from the config'''
    config['active_network']['gas_price'] = 50
    balance = accounts[0].balance()
    tx = accounts[0].transfer(accounts[1], 0)
    assert tx.gas_price == 50
    assert accounts[0].balance() == balance - (50*21000)


def test_transfer_gas_limit_manual():
    '''gas limit is set correctly when specified in the call'''
    tx = accounts[0].transfer(accounts[1], 1000, gas_limit=100000)
    assert tx.gas_limit == 100000
    assert tx.gas_used == 21000


def test_transfer_gas_limit_automatic():
    '''gas limit is set correctly using web3.eth.estimateGas'''
    config['active_network']['gas_limit'] = False
    tx = accounts[0].transfer(accounts[1], 1000)
    assert tx.gas_limit == 21000


def test_transfer_gas_limit_config():
    '''gas limit is set correctly from the config'''
    config['active_network']['gas_limit'] = 50000
    tx = accounts[0].transfer(accounts[1], 1000)
    assert tx.gas_limit == 50000
    assert tx.gas_used == 21000
    config['active_network']['gas_limit'] = False


def test_transfer_data():
    '''transaction data is set correctly'''
    tx = accounts[0].transfer(accounts[1], 1000)
    assert tx.input == "0x"
    tx = accounts[0].transfer(accounts[1], 1000, data="0x1234")
    assert tx.input == "0x1234"


# TODO - deploy tests
