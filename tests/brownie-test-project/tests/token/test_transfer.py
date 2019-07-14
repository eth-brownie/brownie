#!/usr/bin/python3

from brownie import accounts


def test_total_supply(token):
    assert token.totalSupply() == "1000 ether"


def test_transfer(token):
    token.transfer(accounts[1], "0.1 ether", {'from': accounts[0]})
    assert token.balanceOf(accounts[1]) == "0.1 ether"
    assert token.balanceOf(accounts[0]) == "999.9 ether"
