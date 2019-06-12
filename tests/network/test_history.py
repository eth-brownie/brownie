#!/usr/bin/python3

from brownie import history, accounts, rpc


def test_adds_tx(clean_network):
    assert len(history) == 0
    tx = accounts[0].transfer(accounts[1], "1 ether")
    assert tx in history
    assert len(history) == 1
    tx = accounts[2].transfer(accounts[1], "1 ether")
    assert history[-1] == tx
    assert len(history) == 2


def test_resets(clean_network):
    for i in range(3):
        accounts[0].transfer(accounts[1], "1 ether")
    assert len(history) == 3
    rpc.reset()
    assert len(history) == 0


def test_reverts(clean_network):
    for i in range(3):
        accounts[0].transfer(accounts[1], "1 ether")
    rpc.snapshot()
    assert len(history) == 3
    for i in range(3):
        accounts[0].transfer(accounts[1], "1 ether")
    assert len(history) == 6
    tx = history[-1]
    rpc.revert()
    assert len(history) == 3
    assert tx not in history


def test_from(clean_network):
    for i in range(1, 4):
        accounts[0].transfer(accounts[i], "1 ether")
    assert len(history.from_sender(accounts[0])) == 3
    assert len(history.from_sender(accounts[1])) == 0


def test_to(clean_network):
    for i in range(1, 4):
        accounts[0].transfer(accounts[i], "1 ether")
    assert len(history.to_receiver(accounts[0])) == 0
    assert len(history.to_receiver(accounts[1])) == 1
    assert len(history.to_receiver(accounts[2])) == 1
    assert len(history.to_receiver(accounts[3])) == 1


def test_of(clean_network):
    for i in range(4):
        accounts[0].transfer(accounts[i], "1 ether")
    assert len(history.of_address(accounts[0])) == 4
    assert len(history.of_address(accounts[1])) == 1
    assert len(history.of_address(accounts[2])) == 1
    assert len(history.of_address(accounts[3])) == 1
