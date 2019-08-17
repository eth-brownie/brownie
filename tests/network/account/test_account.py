#!/usr/bin/python3

from brownie import Wei


def test_address(accounts, web3):
    '''addresses are set from web3.eth.address'''
    assert web3.eth.accounts[0] == accounts[0].address


def test_estimate_gas(accounts, web3):
    '''gas limit is estimated correctly'''
    assert accounts[0].estimate_gas(accounts[1], 1000) == 21000
    limit = accounts[0].estimate_gas(accounts[1], 1000, data="0x1234")
    assert limit == accounts[0].transfer(accounts[1], 1000, data="0x1234").gas_used


def test_balance(accounts):
    balance = accounts[0].balance()
    assert type(balance) is Wei
    assert balance == "100 ether"
