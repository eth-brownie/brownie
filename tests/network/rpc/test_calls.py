#!/usr/bin/python3

import pytest
import time

from brownie import accounts, config, project, rpc, web3
from brownie.exceptions import RPCRequestError


@pytest.fixture(scope="function")
def noweb3():
    uri = config['active_network']['host']
    web3.disconnect()
    yield
    web3.connect(uri)


def test_time(monkeypatch):
    assert rpc.time() == int(time.time())
    rpc.sleep(25)
    rpc.snapshot()
    rpc.sleep(75)
    assert rpc.time() == int(time.time()+100)
    rpc.revert()
    assert rpc.time() == int(time.time()+25)


def test_time_exceptions(monkeypatch):
    with pytest.raises(TypeError):
        rpc.sleep("foo")
    with pytest.raises(TypeError):
        rpc.sleep(3.0)
    monkeypatch.setattr('brownie.rpc.is_active', lambda: False)
    with pytest.raises(SystemError):
        rpc.time()


def test_mine():
    height = web3.eth.blockNumber
    rpc.mine()
    assert web3.eth.blockNumber == height + 1
    rpc.mine(5)
    assert web3.eth.blockNumber == height + 6


def test_mine_exceptions():
    with pytest.raises(TypeError):
        rpc.mine("foo")
    with pytest.raises(TypeError):
        rpc.mine(3.0)


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


def test_revert_exceptions():
    rpc.reset()
    with pytest.raises(ValueError):
        rpc.revert()


def test_reset():
    accounts[0].transfer(accounts[1], "1 ether")
    project.Token.deploy("", "", 0, 0, {'from': accounts[0]})
    rpc.reset()
    assert web3.eth.blockNumber == 0
    assert accounts[0].balance() == 100000000000000000000
    assert len(project.Token) == 0


def test_request_exceptions(noweb3, monkeypatch):
    with pytest.raises(RPCRequestError):
        rpc.mine()
    monkeypatch.setattr('brownie.rpc.is_active', lambda: False)
    with pytest.raises(SystemError):
        rpc.mine()
