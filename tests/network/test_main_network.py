#!/usr/bin/python3

import pytest


def test_connect(network, rpc, web3):
    network.connect()
    assert network.is_connected()
    assert network.show_active() == "development"
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


def test_connect_ropsten(network):
    network.connect('ropsten')
    assert network.show_active() == "ropsten"


def test_connect_raises_connected(devnetwork):
    with pytest.raises(ConnectionError):
        devnetwork.connect('development')


def test_connect_raises_unknown(network):
    with pytest.raises(KeyError):
        network.connect('thisnetworkdoesntexist')


def test_connect_raises_missing_host(network, config):
    del config['network']['networks']['ropsten']['host']
    with pytest.raises(KeyError):
        network.connect('ropsten')


def test_connect_raises_block_height(network, monkeypatch):
    monkeypatch.setattr('brownie.network.main.is_connected', lambda: True)
    monkeypatch.setattr('brownie.network.web3.manager.request_blocking', lambda *x: 1)
    with pytest.raises(ConnectionError):
        network.connect()


def test_gas_limit_raises_not_connected(network):
    with pytest.raises(ConnectionError):
        network.gas_limit()
    with pytest.raises(ConnectionError):
        network.gas_limit('auto')
    with pytest.raises(ConnectionError):
        network.gas_limit(100000)


def test_gas_limit_manual(devnetwork, config):
    devnetwork.gas_limit(21000)
    assert config['active_network']['gas_limit'] == 21000
    devnetwork.gas_limit(100000)
    assert config['active_network']['gas_limit'] == 100000


def test_gas_limit_auto(devnetwork, config):
    devnetwork.gas_limit(True)
    assert not config['active_network']['gas_limit']
    devnetwork.gas_limit(False)
    assert not config['active_network']['gas_limit']


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


def test_gas_price_manual(devnetwork, config):
    devnetwork.gas_price("1 gwei")
    assert config['active_network']['gas_price'] == 1000000000
    devnetwork.gas_price(100000)
    assert config['active_network']['gas_price'] == 100000


def test_gas_price_auto(devnetwork, config):
    devnetwork.gas_price(None)
    assert not config['active_network']['gas_price']
    devnetwork.gas_price(False)
    assert not config['active_network']['gas_price']


def test_gas_price_raises(devnetwork):
    with pytest.raises(TypeError):
        devnetwork.gas_price("potato")
