#!/usr/bin/python3

from pathlib import Path

import pytest

priv_key = "0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09"
addr = "0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E"


@pytest.fixture(autouse=True)
def no_pass(monkeypatch):
    monkeypatch.setattr("brownie.network.account.getpass", lambda x: "")


def test_save(accounts, tmpdir):
    a = accounts.add(priv_key)
    a.save(tmpdir + "/temp.json")
    assert Path(tmpdir + "/temp.json").exists()
    accounts._reset()


def test_save_nopath(accounts, tmpdir):
    a = accounts.add(priv_key)
    path = Path(a.save("temp", True))
    assert path.exists()
    path.unlink()
    Path(a.save("temp"))
    assert path.exists()
    path.unlink()
    accounts._reset()


def test_save_overwrite(accounts, tmpdir):
    a = accounts.add(priv_key)
    a.save(tmpdir + "/temp.json")
    with pytest.raises(FileExistsError):
        a.save(tmpdir + "/temp.json")
    a.save(tmpdir + "/temp.json", True)
    accounts._reset()


def test_load(accounts, tmpdir):
    a = accounts.add(priv_key)
    a.save(tmpdir + "/temp.json")
    accounts._reset()
    assert a not in accounts
    a = accounts.load(tmpdir + "/temp.json")
    assert a.address == addr


def test_load_nopath(accounts, tmpdir):
    a = accounts.add(priv_key)
    path = a.save("temp")
    accounts._reset()
    a = accounts.load("temp")
    assert a.address == addr
    Path(path).unlink()


def test_load_not_exists(accounts, tmpdir):
    with pytest.raises(FileNotFoundError):
        accounts.load(tmpdir + "/temp.json")
    with pytest.raises(FileNotFoundError):
        accounts.load("temp")
