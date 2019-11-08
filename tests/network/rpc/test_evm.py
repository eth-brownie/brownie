#!/usr/bin/python3

import pytest

from brownie import rpc
from brownie.exceptions import RPCRequestError


def test_inactive(monkeypatch):
    monkeypatch.setattr("brownie.rpc.is_active", lambda: False)
    assert rpc.evm_version() is None
    with pytest.raises(RPCRequestError):
        rpc.evm_compatible("byzantium")


def test_evm_version_default(monkeypatch):
    monkeypatch.setattr("psutil.Popen.cmdline", lambda s: ["-k", "potato"])
    assert rpc.evm_version() == "potato"
    monkeypatch.setattr("psutil.Popen.cmdline", lambda s: ["--hardfork", "otatop"])
    assert rpc.evm_version() == "otatop"
    monkeypatch.setattr("psutil.Popen.cmdline", lambda s: ["--hardfork"])
    assert rpc.evm_version() == "petersburg"


def test_evm_compatible(monkeypatch):
    monkeypatch.setattr("psutil.Popen.cmdline", lambda s: ["-k", "constantinople"])
    assert rpc.evm_compatible("byzantium")
    assert rpc.evm_compatible("constantinople")
    assert not rpc.evm_compatible("petersburg")
    with pytest.raises(ValueError):
        rpc.evm_compatible("potato")
