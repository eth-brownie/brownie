#!/usr/bin/python3

import time

import pytest


@pytest.fixture
def noweb3(config, web3):
    uri = config["active_network"]["host"]
    web3.disconnect()
    yield
    web3.connect(uri)


def test_time(devnetwork, chain):
    assert chain.time() == int(time.time())
    chain.sleep(25)
    chain.snapshot()
    chain.sleep(75)
    assert chain.time() == int(time.time() + 100)
    chain.revert()
    assert chain.time() == int(time.time() + 25)


def test_time_exceptions(devnetwork, chain):
    with pytest.raises(TypeError):
        chain.sleep("foo")
    with pytest.raises(TypeError):
        chain.sleep(3.0)


def test_mine(devnetwork, chain, web3):
    height = web3.eth.block_number
    chain.mine()
    assert web3.eth.block_number == height + 1
    chain.mine(5)
    assert web3.eth.block_number == height + 6


def test_mine_exceptions(devnetwork, chain):
    with pytest.raises(TypeError):
        chain.mine("foo")
    with pytest.raises(TypeError):
        chain.mine(3.0)


def test_snapshot_revert(BrownieTester, accounts, chain, web3):
    height = web3.eth.block_number
    balance = accounts[0].balance()
    count = len(BrownieTester)
    chain.snapshot()
    accounts[0].transfer(accounts[1], "1 ether")
    BrownieTester.deploy(True, {"from": accounts[0]})
    chain.revert()
    assert height == web3.eth.block_number
    assert balance == accounts[0].balance()
    assert count == len(BrownieTester)
    chain.revert()
    assert height == web3.eth.block_number
    assert balance == accounts[0].balance()
    assert count == len(BrownieTester)


def test_revert_exceptions(devnetwork, chain):
    chain.reset()
    with pytest.raises(ValueError):
        chain.revert()


def test_reset(BrownieTester, accounts, chain, web3):
    accounts[0].transfer(accounts[1], "1 ether")
    BrownieTester.deploy(True, {"from": accounts[0]})
    chain.reset()
    assert web3.eth.block_number == 0
    assert accounts[0].balance() == 1000000000000000000000
    assert len(BrownieTester) == 0
