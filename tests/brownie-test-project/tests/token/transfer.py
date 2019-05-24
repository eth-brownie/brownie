#!/usr/bin/python3

from brownie import project, accounts, check
import scripts.token


def setup():
    scripts.token.main()


def transfer():
    '''Transfer tokens'''
    token = project.Token[0]
    check.equal(token.totalSupply(), "1000 ether", "totalSupply is wrong")
    token.transfer(accounts[1], "0.1 ether", {'from': accounts[0]})
    check.equal(
        token.balanceOf(accounts[1]),
        "0.1 ether",
        "Accounts 1 balance is wrong"
    )
    check.equal(
        token.balanceOf(accounts[0]),
        "999.9 ether",
        "Accounts 0 balance is wrong"
    )
