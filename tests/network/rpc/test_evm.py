#!/usr/bin/python3

import pytest

from brownie._config import EVM_EQUIVALENTS
from brownie.exceptions import RPCRequestError


def test_inactive(monkeypatch, rpc):
    monkeypatch.setattr("brownie.rpc.is_active", lambda: False)
    assert rpc.evm_version() is None
    with pytest.raises(RPCRequestError):
        rpc.evm_compatible("byzantium")


def test_evm_version_default(monkeypatch, rpc):
    monkeypatch.setattr("psutil.Popen.cmdline", lambda s: ["-k", "potato"])
    assert rpc.evm_version() == "potato"
    monkeypatch.setattr("psutil.Popen.cmdline", lambda s: ["--hardfork", "otatop"])
    assert rpc.evm_version() == "otatop"
    monkeypatch.setattr("psutil.Popen.cmdline", lambda s: ["--hardfork"])
    assert rpc.evm_version() == "istanbul"


def test_evm_compatible(monkeypatch, rpc):
    monkeypatch.setattr("psutil.Popen.cmdline", lambda s: ["-k", "constantinople"])
    assert rpc.evm_compatible("byzantium")
    assert rpc.evm_compatible("constantinople")
    assert not rpc.evm_compatible("petersburg")
    with pytest.raises(ValueError):
        rpc.evm_compatible("potato")


@pytest.mark.parametrize("original,translated", EVM_EQUIVALENTS.items())
def test_evm_equivalents(no_rpc, temp_port, original, translated):
    assert not no_rpc.is_active()
    no_rpc.launch("ganache-cli", port=temp_port, evm_version=original)
    assert no_rpc.is_active()
    assert no_rpc.evm_version() == translated
    no_rpc.kill()
