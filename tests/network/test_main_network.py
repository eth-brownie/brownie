#!/usr/bin/python3

import pytest


def test_connect(network, rpc, web3, network_name):
    network.connect(network_name)
    assert network.is_connected()
    assert network.show_active() == network_name
    assert rpc.is_active()
    assert web3.isConnected()


def test_disconnect(devnetwork, rpc, web3):
    devnetwork.disconnect()
    assert not devnetwork.is_connected()
    assert devnetwork.show_active() is None
    assert not rpc.is_active()
    assert not web3.isConnected()
    with pytest.raises(ConnectionError):
        devnetwork.disconnect()


def test_connect_goerli(network):
    network.connect("goerli")
    assert network.show_active() == "goerli"


def test_connect_raises_connected(devnetwork):
    with pytest.raises(ConnectionError):
        devnetwork.connect("development")


def test_connect_raises_unknown(network):
    with pytest.raises(KeyError):
        network.connect("thisnetworkdoesntexist")


def test_gas_limit_raises_not_connected(network):
    with pytest.raises(ConnectionError):
        network.gas_limit()
    with pytest.raises(ConnectionError):
        network.gas_limit("auto")
    with pytest.raises(ConnectionError):
        network.gas_limit(100000)


def test_gas_limit_manual(devnetwork, accounts):
    devnetwork.gas_limit(100000)
    tx = accounts[0].transfer(accounts[1], 0)
    assert tx.gas_limit == 100000


def test_gas_limit_auto(devnetwork, accounts):
    devnetwork.gas_limit("auto")
    tx = accounts[0].transfer(accounts[1], 0)
    assert tx.gas_limit == 21000


def test_gas_limit_raises(devnetwork):
    with pytest.raises(ValueError):
        devnetwork.gas_limit(20999)
    with pytest.raises(TypeError):
        devnetwork.gas_limit("potato")


def test_gas_price_raises_not_connected(network):
    with pytest.raises(ConnectionError):
        network.gas_price()
    with pytest.raises(ConnectionError):
        network.gas_price(False)
    with pytest.raises(ConnectionError):
        network.gas_price(100000)


def test_gas_price_manual(devnetwork, accounts):
    devnetwork.gas_price(1000000)
    tx = accounts[0].transfer(accounts[1], 0)
    assert tx.gas_price == 1000000


def test_gas_price_auto(devnetwork, accounts, web3):
    devnetwork.gas_price(None)
    tx = accounts[0].transfer(accounts[1], 0)
    assert tx.gas_price == web3.eth.gas_price


def test_gas_price_raises(devnetwork):
    with pytest.raises(TypeError):
        devnetwork.gas_price("potato")
