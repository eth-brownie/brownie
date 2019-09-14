#!/usr/bin/python3

import pytest
import time

from brownie.exceptions import RPCRequestError


@pytest.fixture
def noweb3(config, web3):
    uri = config["active_network"]["host"]
    web3.disconnect()
    yield
    web3.connect(uri)


def test_time(devnetwork, rpc):
    assert rpc.time() == int(time.time())
    rpc.sleep(25)
    rpc.snapshot()
    rpc.sleep(75)
    assert rpc.time() == int(time.time() + 100)
    rpc.revert()
    assert rpc.time() == int(time.time() + 25)


def test_time_exceptions(devnetwork, rpc, monkeypatch):
    with pytest.raises(TypeError):
        rpc.sleep("foo")
    with pytest.raises(TypeError):
        rpc.sleep(3.0)
    monkeypatch.setattr("brownie.rpc.is_active", lambda: False)
    with pytest.raises(SystemError):
        rpc.time()


def test_mine(devnetwork, rpc, web3):
    height = web3.eth.blockNumber
    rpc.mine()
    assert web3.eth.blockNumber == height + 1
    rpc.mine(5)
    assert web3.eth.blockNumber == height + 6


def test_mine_exceptions(devnetwork, rpc):
    with pytest.raises(TypeError):
        rpc.mine("foo")
    with pytest.raises(TypeError):
        rpc.mine(3.0)


def test_snapshot_revert(BrownieTester, accounts, rpc, web3):
    height = web3.eth.blockNumber
    balance = accounts[0].balance()
    count = len(BrownieTester)
    rpc.snapshot()
    accounts[0].transfer(accounts[1], "1 ether")
    BrownieTester.deploy(True, {"from": accounts[0]})
    rpc.revert()
    assert height == web3.eth.blockNumber
    assert balance == accounts[0].balance()
    assert count == len(BrownieTester)
    rpc.revert()
    assert height == web3.eth.blockNumber
    assert balance == accounts[0].balance()
    assert count == len(BrownieTester)


def test_revert_exceptions(devnetwork, rpc):
    rpc.reset()
    with pytest.raises(ValueError):
        rpc.revert()


def test_reset(BrownieTester, accounts, rpc, web3):
    accounts[0].transfer(accounts[1], "1 ether")
    BrownieTester.deploy(True, {"from": accounts[0]})
    rpc.reset()
    assert web3.eth.blockNumber == 0
    assert accounts[0].balance() == 100000000000000000000
    assert len(BrownieTester) == 0


def test_request_exceptions(devnetwork, rpc, noweb3, monkeypatch):
    with pytest.raises(RPCRequestError):
        rpc.mine()
    monkeypatch.setattr("brownie.rpc.is_active", lambda: False)
    with pytest.raises(SystemError):
        rpc.mine()
