#!/usr/bin/python3

import pytest

from brownie._cli.networks import DEV_CMD_SETTINGS
from brownie.network.rpc import anvil

pytestmark = pytest.mark.backend("anvil")


@pytest.fixture
def popen_calls(monkeypatch):
    calls = []

    def popen(cmd_list, **kwargs):
        calls.append((cmd_list, kwargs))
        return object()

    monkeypatch.setattr(anvil.psutil, "Popen", popen)
    return calls


def test_anvil_launcher_keeps_falsy_command_values(popen_calls):
    anvil.launch(
        "anvil",
        base_fee=0,
        gas_price=0,
        fork=None,
        block_time=False,
        steps_tracing=True,
    )

    cmd_list, _ = calls.pop()

    assert cmd_list == [
        "anvil",
        "--quiet",
        "--block-base-fee-per-gas",
        "0",
        "--gas-price",
        "0",
        "--steps-tracing",
    ]
    assert "--fork-url" not in cmd_list
    assert "--block-time" not in cmd_list


def test_anvil_launcher_does_not_set_default_balance(popen_calls):
    anvil.launch("anvil")

    cmd_list, _ = popen_calls.pop()
    assert "--balance" not in cmd_list


def test_anvil_launcher_preserves_explicit_default_balance(popen_calls):
    anvil.launch("anvil", default_balance=42)

    cmd_list, _ = popen_calls.pop()
    assert cmd_list[cmd_list.index("--balance") + 1] == "42"


def test_anvil_cli_settings_are_allowed():
    assert "gas_price" in DEV_CMD_SETTINGS
    assert "base_fee" in DEV_CMD_SETTINGS
    assert "steps_tracing" in DEV_CMD_SETTINGS
