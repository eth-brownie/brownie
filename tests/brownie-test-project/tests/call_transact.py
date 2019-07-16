#!/usr/bin/python3

from brownie import accounts, web3


def test_call_and_transact(Token):
    token = accounts[0].deploy(Token, "Test Token", "TST", 18, "1000 ether")
    token.transfer(accounts[1], "10 ether", {'from': accounts[0]})
    assert web3.eth.blockNumber == 2
    assert token.balanceOf(accounts[1]) == "10 ether"
    assert web3.eth.blockNumber == 2
