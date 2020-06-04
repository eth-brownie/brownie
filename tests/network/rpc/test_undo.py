#!/usr/bin/python3

import pytest


def test_undo(accounts, rpc, web3):
    initial = accounts[0].balance()
    accounts[0].transfer(accounts[1], "1 ether")
    rpc.undo()
    assert web3.eth.blockNumber == 0
    assert accounts[0].balance() == initial


def test_undo_multiple(accounts, rpc, web3):
    initial = accounts[0].balance()
    for i in range(1, 6):
        accounts[0].transfer(accounts[i], "1 ether")
    rpc.undo(5)
    assert accounts[0].balance() == initial


def test_undo_empty_buffer(accounts, rpc):
    with pytest.raises(ValueError):
        rpc.undo()


def test_undo_zero(accounts, rpc):
    accounts[0].transfer(accounts[1], 100)
    with pytest.raises(ValueError):
        rpc.undo(0)


def test_undo_too_many(accounts, rpc):
    accounts[0].transfer(accounts[1], 100)
    with pytest.raises(ValueError):
        rpc.undo(2)


def test_snapshot_clears_undo_buffer(accounts, rpc):
    accounts[0].transfer(accounts[1], 100)
    rpc.snapshot()
    with pytest.raises(ValueError):
        rpc.undo()


def test_revert_clears_undo_buffer(accounts, rpc):
    accounts[0].transfer(accounts[1], 100)
    rpc.snapshot()
    accounts[0].transfer(accounts[1], 100)
    rpc.revert()
    with pytest.raises(ValueError):
        rpc.undo()


def test_does_not_undo_sleep(accounts, rpc):
    accounts[0].transfer(accounts[1], 100)
    time = rpc.time()
    rpc.sleep(100000)
    accounts[0].transfer(accounts[1], 100)
    rpc.undo()
    assert rpc.time() >= time + 100000


def test_does_not_undo_mining(accounts, rpc, web3):
    accounts[0].transfer(accounts[1], 100)
    rpc.mine()
    height = web3.eth.blockNumber
    accounts[0].transfer(accounts[1], 100)
    rpc.undo()
    assert web3.eth.blockNumber == height
