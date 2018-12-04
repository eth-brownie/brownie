#!/usr/bin/python3

DEPLOYMENT = "token"

def approve():
    '''Set approval'''
    global token
    token = Token[0]
    token.approve(accounts[1], "10 ether", {'from':accounts[0]})
    check.equal(token.allowance(accounts[0], accounts[1]), "10 ether", "Allowance is wrong")
    check.equal(token.allowance(accounts[0], accounts[2]), 0, "Allowance is wrong")
    token.approve(accounts[1], "6 ether", {'from':accounts[0]})
    check.equal(token.allowance(accounts[0], accounts[1]), "6 ether", "Allowance is wrong")

def transfer():
    '''Transfer tokens with transferFrom'''
    token.transferFrom(accounts[0], accounts[2], "5 ether", {'from':accounts[1]})
    check.equal(token.balanceOf(accounts[2]), "5 ether", "Accounts 2 balance is wrong")
    check.equal(token.balanceOf(accounts[1]), 0, "Accounts 1 balance is wrong")
    check.equal(token.balanceOf(accounts[0]), "995 ether", "Accounts 0 balance is wrong")
    check.equal(token.allowance(accounts[0], accounts[1]), "1 ether", "Allowance is wrong")

def revert():
    '''transerFrom should revert'''
    check.reverts(
        token.transferFrom,
        (accounts[0], accounts[3], "10 ether", {'from':accounts[1]}),
        "transferFrom did not revert")
    check.reverts(
        token.transferFrom,
        (accounts[0], accounts[2], "1 ether", {'from':accounts[0]}),
        "transferFrom did not revert")