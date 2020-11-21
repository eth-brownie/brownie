#!/usr/bin/python3

import pytest
from web3 import HTTPProvider, IPCProvider, Web3, WebsocketProvider

from brownie.exceptions import MainnetUndefined


def test_connect_http(web3):
    web3.connect("http://localhost")
    assert type(web3.provider) is HTTPProvider
    web3.disconnect()


def test_connect_https(web3):
    web3.connect("https://localhost")
    assert type(web3.provider) is HTTPProvider
    web3.disconnect()


def test_connect_ipc(web3, testdir):
    web3.connect(str(testdir))
    assert type(web3.provider) is IPCProvider
    web3.disconnect()


def test_connect_ws(web3):
    web3.connect("ws://localhost")
    assert type(web3.provider) is WebsocketProvider
    web3.disconnect()


def test_connect_raises(web3):
    with pytest.raises(ValueError):
        web3.connect("foo")


def test_bad_env_var(web3):
    with pytest.raises(ValueError):
        web3.connect("https://$POTATO")


def test_mainnet(config, network, web3):
    assert type(web3._mainnet) == Web3
    assert web3._mainnet != web3
    network.connect("mainnet")
    assert web3._mainnet == web3
    network.disconnect()
    del config.networks["mainnet"]
    with pytest.raises(MainnetUndefined):
        web3._mainnet


# TODO mainnet undefined


def test_disconnect(web3):
    web3.disconnect()
    assert not web3.provider
    web3.disconnect()
    web3.connect("https://localhost")
    assert web3.provider
    web3.disconnect()
    assert not web3.provider


def test_genesis_hash(web3, devnetwork):
    assert web3.genesis_hash == web3.eth.getBlock(0)["hash"].hex()[2:]


def test_genesis_hash_different_networks(devnetwork, web3):
    ganache_hash = web3.genesis_hash
    devnetwork.disconnect()
    devnetwork.connect("ropsten")
    assert web3.genesis_hash == "41941023680923e0fe4d74a34bdac8141f2540e3ae90623718e47d66d1ca4a2d"
    assert web3.genesis_hash != ganache_hash


def test_genesis_hash_disconnected(web3):
    web3.disconnect()
    with pytest.raises(ConnectionError):
        web3.genesis_hash


def test_chain_uri(web3, network):
    network.connect("ropsten")
    assert web3.chain_uri.startswith(
        "blockchain://41941023680923e0fe4d74a34bdac8141f2540e3ae90623718e47d66d1ca4a2d/block/"
    )


def test_chain_uri_disconnected(web3):
    web3.disconnect()
    with pytest.raises(ConnectionError):
        web3.chain_uri


def test_rinkeby(web3, network):
    network.connect("rinkeby")

    # this should work because we automatically add the POA middleware
    web3.eth.getBlock("latest")


def test_supports_traces_development(web3, devnetwork):
    # development should return true
    assert web3.supports_traces


def test_supports_traces_not_connected(web3, network):
    # should return false when disconnected
    assert not web3.supports_traces


def test_supports_traces_infura(web3, network):
    # ropsten should return false (infura, geth)
    network.connect("ropsten")
    assert not web3.supports_traces


def test_supports_traces_kovan(web3, network):
    # kovan should return false (infura, parity)
    network.connect("kovan")

    assert not web3.supports_traces
