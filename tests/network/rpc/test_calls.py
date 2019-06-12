#!/usr/bin/python3

import time

from brownie import accounts, project, rpc, web3


def test_time():
    assert rpc.time() == int(time.time())
    rpc.sleep(25)
    rpc.snapshot()
    rpc.sleep(75)
    assert rpc.time() == int(time.time()+100)
    rpc.revert()
    assert rpc.time() == int(time.time()+25)


def test_mine():
    height = web3.eth.blockNumber
    rpc.mine()
    assert web3.eth.blockNumber == height + 1
    rpc.mine(5)
    assert web3.eth.blockNumber == height + 6


def test_snapshot_revert():
    height = web3.eth.blockNumber
    balance = accounts[0].balance()
    count = len(project.Token)
    rpc.snapshot()
    accounts[0].transfer(accounts[1], "1 ether")
    project.Token.deploy("", "", 0, 0, {'from': accounts[0]})
    rpc.revert()
    assert height == web3.eth.blockNumber
    assert balance == accounts[0].balance()
    assert count == len(project.Token)
    rpc.revert()
    assert height == web3.eth.blockNumber
    assert balance == accounts[0].balance()
    assert count == len(project.Token)


def test_reset():
    accounts[0].transfer(accounts[1], "1 ether")
    project.Token.deploy("", "", 0, 0, {'from': accounts[0]})
    rpc.reset()
    assert web3.eth.blockNumber == 0
    assert accounts[0].balance() == 100000000000000000000
    assert len(project.Token) == 0
