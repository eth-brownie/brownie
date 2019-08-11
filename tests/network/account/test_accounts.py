#!/usr/bin/python3

import pytest

from brownie.exceptions import UnknownAccount

priv_key = "0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09"
addr = "0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E"


def test_repopulate(accounts, network, rpc, config):
    assert len(accounts) > 0
    a = list(accounts)
    rpc.reset()
    assert a == list(accounts)
    network.disconnect()
    assert len(accounts) == 0
    assert not rpc.is_active()
    del config['networks']['development']['test_rpc']['mnemonic']
    network.connect('development')
    assert len(accounts) > 0


def test_add(devnetwork, accounts):
    assert len(accounts) == 10
    accounts.add()
    assert len(accounts) == 11
    accounts.add(priv_key)
    assert len(accounts) == 12
    assert accounts[-1].address == addr
    assert accounts[-1].private_key == priv_key
    accounts._reset()


def test_at(accounts):
    with pytest.raises(UnknownAccount):
        accounts.at(addr)
    a = accounts.add(priv_key)
    assert a == accounts.at(addr)
    assert a == accounts.at(a)
    accounts._reset()


def test_remove(accounts):
    assert len(accounts) == 10
    with pytest.raises(UnknownAccount):
        accounts.remove(addr)
    a = accounts.add(priv_key)
    accounts.remove(a)
    with pytest.raises(UnknownAccount):
        accounts.remove(a)
    accounts.add(priv_key)
    accounts.remove(addr)
    accounts.add(priv_key)
    accounts.remove(addr.lower())
    accounts._reset()


def test_clear(accounts):
    assert len(accounts) == 10
    accounts.clear()
    assert len(accounts) == 0
    accounts._reset()
