#!/usr/bin/python3

from brownie import network

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
