#!/usr/bin/python3

import pytest


def test_undo(accounts, chain, web3):
    initial = accounts[0].balance()
    accounts[0].transfer(accounts[1], "1 ether")
    chain.undo()
    assert web3.eth.block_number == 0
    assert accounts[0].balance() == initial


def test_undo_multiple(accounts, chain, web3):
    initial = accounts[0].balance()
    for i in range(1, 6):
        accounts[0].transfer(accounts[i], f"{i} ether")
    chain.undo(5)
    assert accounts[0].balance() == initial


def test_undo_empty_buffer(accounts, chain):
    with pytest.raises(ValueError):
        chain.undo()


def test_undo_zero(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    with pytest.raises(ValueError):
        chain.undo(0)


def test_undo_too_many(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    with pytest.raises(ValueError):
        chain.undo(2)


def test_snapshot_clears_undo_buffer(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    chain.snapshot()
    with pytest.raises(ValueError):
        chain.undo()


def test_revert_clears_undo_buffer(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    chain.snapshot()
    accounts[0].transfer(accounts[1], 100)
    chain.revert()
    with pytest.raises(ValueError):
        chain.undo()


def test_does_not_undo_sleep(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    time = chain.time()
    chain.sleep(100000)
    accounts[0].transfer(accounts[1], 100)
    chain.undo()
    assert chain.time() >= time + 100000


def test_does_not_undo_mining(accounts, chain, web3):
    accounts[0].transfer(accounts[1], 100)
    chain.mine()
    height = web3.eth.block_number
    accounts[0].transfer(accounts[1], 100)
    chain.undo()
    assert web3.eth.block_number == height
