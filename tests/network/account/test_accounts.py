#!/usr/bin/python3

from pathlib import Path
import pytest


from brownie import network
from brownie.exceptions import UnknownAccount

accounts = network.accounts
priv_key = "0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09"
addr = "0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E"


@pytest.fixture
def no_pass(monkeypatch):
    monkeypatch.setattr('brownie.network.account.getpass', lambda x: "")
    yield


def test_repopulate():
    network.rpc.reset()
    assert len(accounts) == 10
    a = list(accounts)
    network.rpc.reset()
    assert a == list(accounts)
    network.disconnect()
    assert len(accounts) == 0
    network.connect('development')
    assert len(accounts) == 10
    assert a != list(accounts)


def test_add():
    assert len(accounts) == 10
    accounts.add()
    assert len(accounts) == 11
    accounts.add(priv_key)
    assert len(accounts) == 12
    assert accounts[-1].address == addr
    assert accounts[-1].private_key == priv_key
    accounts._reset()


def test_at():
    with pytest.raises(UnknownAccount):
        accounts.at(addr)
    a = accounts.add(priv_key)
    assert a == accounts.at(addr)
    assert a == accounts.at(a)
    accounts._reset()


def test_remove():
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


def test_clear():
    assert len(accounts) == 10
    accounts.clear()
    assert len(accounts) == 0
    accounts._reset()


def test_save(tmpdir, no_pass):
    a = accounts.add(priv_key)
    a.save(tmpdir+"/temp.json")
    assert Path(tmpdir+"/temp.json").exists()
    accounts._reset()


def test_save_nopath(no_pass):
    a = accounts.add(priv_key)
    path = Path(a.save("temp", True))
    assert path.exists()
    path.unlink()
    Path(a.save("temp"))
    assert path.exists()
    path.unlink()
    accounts._reset()


def test_save_overwrite(tmpdir, no_pass):
    a = accounts.add(priv_key)
    a.save(tmpdir+"/temp.json")
    with pytest.raises(FileExistsError):
        a.save(tmpdir+"/temp.json")
    a.save(tmpdir+"/temp.json", True)
    accounts._reset()


def test_load(tmpdir, no_pass):
    a = accounts.add(priv_key)
    a.save(tmpdir+"/temp.json")
    accounts._reset()
    assert a not in accounts
    a = accounts.load(tmpdir+"/temp.json")
    assert a.address == addr


def test_load_nopath(no_pass):
    a = accounts.add(priv_key)
    path = a.save("temp")
    accounts._reset()
    a = accounts.load("temp")
    assert a.address == addr
    Path(path).unlink()


def test_load_not_exists(tmpdir, no_pass):
    with pytest.raises(FileNotFoundError):
        accounts.load(tmpdir+"/temp.json")
    with pytest.raises(FileNotFoundError):
        accounts.load("temp")
