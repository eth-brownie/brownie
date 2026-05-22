#!/usr/bin/python3

import pytest

from brownie.network.rpc import ganache


@pytest.fixture
def popen_calls(monkeypatch):
    calls = []

    def popen(cmd_list, **kwargs):
        calls.append((cmd_list, kwargs))

    monkeypatch.setattr(ganache.psutil, "Popen", popen)
    return calls


@pytest.mark.parametrize(
    "version,flag",
    [
        (6, "--defaultBalanceEther"),
        (7, "--wallet.defaultBalance"),
    ],
)
def test_launch_sets_default_balance(monkeypatch, popen_calls, version, flag):
    monkeypatch.setattr(ganache, "get_ganache_version", lambda _: version)

    ganache.launch("ganache-cli")

    cmd_list, _ = popen_calls.pop()
    assert cmd_list[cmd_list.index(flag) + 1] == "100"


def test_launch_preserves_explicit_default_balance(monkeypatch, popen_calls):
    monkeypatch.setattr(ganache, "get_ganache_version", lambda _: 7)

    ganache.launch("ganache-cli", default_balance=42)

    cmd_list, _ = popen_calls.pop()
    assert cmd_list[cmd_list.index("--wallet.defaultBalance") + 1] == "42"
