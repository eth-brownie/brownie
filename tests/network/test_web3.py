#!/usr/bin/python3

import pytest
from web3 import HTTPProvider, IPCProvider, WebsocketProvider


def test_connect_http(web3):
    web3.connect("http://localhost")
    assert type(web3.provider) is HTTPProvider


def test_connect_https(web3):
    web3.connect("https://localhost")
    assert type(web3.provider) is HTTPProvider


def test_connect_ipc(web3, testdir):
    web3.connect(str(testdir))
    assert type(web3.provider) is IPCProvider


def test_connect_ws(web3):
    web3.connect("ws://localhost")
    assert type(web3.provider) is WebsocketProvider


def test_connect_raises(web3):
    with pytest.raises(ValueError):
        web3.connect("foo")


def test_disconnect(web3):
    web3.disconnect()
    assert not web3.provider
    web3.disconnect()
    web3.connect("https://localhost")
    assert web3.provider
    web3.disconnect()
    assert not web3.provider
