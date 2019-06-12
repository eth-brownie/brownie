#!/usr/bin/python3

import pytest

from brownie import network, rpc, web3, config


@pytest.fixture(autouse=True, scope="module")
def setup():
    network.disconnect()
    yield
    if not network.is_connected():
        network.connect('development')
    elif network.show_active() != "development":
        network.disconnect()
        network.connect('development')


def test_connect():
    network.connect()
    assert network.is_connected()
    assert network.show_active() == "development"
    assert rpc.is_active()
    assert web3.isConnected()


def test_disconnect():
    network.disconnect()
    assert not network.is_connected()
    assert network.show_active() is None
    assert not rpc.is_active()
    assert not web3.isConnected()
    with pytest.raises(ConnectionError):
        network.disconnect()


def test_connect_ropsten():
    try:
        network.connect('ropsten')
        assert network.show_active() == "ropsten"
    except Exception:
        network.connect('development')
        raise


def test_connect_raises_connected():
    with pytest.raises(ConnectionError):
        network.connect('development')
    network.disconnect()


def test_connect_raises_unknown():
    with pytest.raises(KeyError):
        network.connect('thisnetworkdoesntexist')


def test_connect_raises_missing_host():
    host = config['networks']['ropsten']['host']
    del config['networks']['ropsten']['host']
    with pytest.raises(KeyError):
        network.connect('ropsten')
    config._unlock()
    config['networks']['ropsten']['host'] = host


def test_connect_raises_block_height(monkeypatch):
    monkeypatch.setattr('brownie.network.main.is_connected', lambda: True)
    monkeypatch.setattr('brownie.network.web3.manager.request_blocking', lambda *x: 1)
    with pytest.raises(ConnectionError):
        network.connect()


def test_gas_limit_raises_not_connected():
    with pytest.raises(ConnectionError):
        network.gas_limit()
    with pytest.raises(ConnectionError):
        network.gas_limit('auto')
    with pytest.raises(ConnectionError):
        network.gas_limit(100000)


def test_gas_limit_manual():
    network.connect('ropsten')
    network.gas_limit(21000)
    assert config['active_network']['gas_limit'] == 21000
    network.gas_limit(100000)
    assert config['active_network']['gas_limit'] == 100000


def test_gas_limit_auto():
    network.gas_limit('auto')
    assert not config['active_network']['gas_limit']
    network.gas_limit(False)
    assert not config['active_network']['gas_limit']


def test_gas_limit_raises():
    with pytest.raises(ValueError):
        network.gas_limit(2000)
    with pytest.raises(TypeError):
        network.gas_limit("potato")
