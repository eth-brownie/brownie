#!/usr/bin/python3

import pytest

from brownie.exceptions import UnknownAccount
from brownie.network.account import LocalAccount

priv_key = "0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09"
addr = "0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E"


def test_repopulate(accounts, network, rpc):
    assert len(accounts) > 0
    a = list(accounts)
    rpc.reset()
    assert len(accounts) == len(a)
    for i in range(len(a)):
        assert a[i] != accounts[i]
        assert str(a[i]) == str(accounts[i])
    network.disconnect()
    assert len(accounts) == 0
    assert not rpc.is_active()
    network.connect('development')
    assert len(accounts) == len(a)


def test_contains(accounts):
    assert accounts[-1] in accounts
    assert str(accounts[-1]) in accounts
    assert "potato" not in accounts
    assert 12345 not in accounts


def test_add(devnetwork, accounts):
    assert len(accounts) == 10
    local = accounts.add()
    assert len(accounts) == 11
    assert type(local) is LocalAccount
    assert accounts[-1] == local
    accounts.add(priv_key)
    assert len(accounts) == 12
    assert accounts[-1].address == addr
    assert accounts[-1].private_key == priv_key
    accounts.add(priv_key)
    assert len(accounts) == 12


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


def test_delete(accounts):
    assert len(accounts) == 10
    a = accounts[-1]
    del accounts[-1]
    assert len(accounts) == 9
    assert a not in accounts
