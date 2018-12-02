#!/usr/bin/python3

DEPLOYMENT = "deploy"



def transfer():
    '''Transfer tokens'''
    global token
    token = Token[0]
    check.equal(token.totalSupply(), "1000 ether", "totalSupply is wrong")
    token.transfer(accounts[1], "0.1 ether", {'from':accounts[0]})
    check.equal(token.balanceOf(accounts[1]), "0.1 ether", "Accounts 1 balance is wrong")
    check.equal(token.balanceOf(accounts[0]), "999.9 ether", "Accounts 1 balance is wrong")
    