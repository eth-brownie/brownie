#!/usr/bin/python3

import pytest

from brownie.network.rpc import ganache

pytestmark = pytest.mark.backend("ganache")


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


@pytest.fixture
def provider(monkeypatch):
    class Provider:
        def __init__(self):
            self.calls = []

        def make_request(self, method, args):
            self.calls.append((method, args))
            return {"result": 0}

    provider = Provider()
    monkeypatch.setattr(ganache.web3, "provider", provider)
    return provider


def test_mine_timestamp_sets_ganache7_clock(monkeypatch, provider):
    monkeypatch.setattr(ganache, "_is_ganache_v7", lambda: True)

    ganache.mine(123)

    assert provider.calls == [
        ("evm_setTime", [123000]),
        ("evm_mine", []),
        ("evm_setTime", [124000]),
    ]


def test_mine_timestamp_uses_legacy_param_for_ganache6(monkeypatch, provider):
    monkeypatch.setattr(ganache, "_is_ganache_v7", lambda: False)

    ganache.mine(123)

    assert provider.calls == [("evm_mine", [123])]


def test_mine_without_timestamp_mines_one_block(provider):
    ganache.mine()

    assert provider.calls == [("evm_mine", [])]
