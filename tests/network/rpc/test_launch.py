#!/usr/bin/python3

import pytest

import brownie
from brownie.exceptions import RPCProcessError

pytestmark = pytest.mark.backend("anvil")


def test_launch_file_not_found(no_rpc):
    with pytest.raises(FileNotFoundError):
        no_rpc.launch("not-anvil")


def test_launch_process_fails(no_rpc):
    with pytest.raises(RPCProcessError):
        no_rpc.launch("anvil --help")


def test_launch(no_rpc, temp_port):
    assert not no_rpc.is_active()
    assert not no_rpc.is_child()
    no_rpc.launch("anvil", port=temp_port)
    assert no_rpc.is_active()
    assert no_rpc.is_child()


def test_launch_with_mnemonic(no_rpc, temp_port):
    no_rpc.kill(False)
    no_rpc.launch(
        "anvil",
        port=temp_port,
        mnemonic="patient rude simple dog close planet oval animal hunt sketch suspect slim",
    )
    assert brownie.network.accounts[0] == "0x7cB87a59C85a0c6d8E2953ed54f1c9E4C28E25E5"


def test_already_active(temp_rpc, temp_port):
    with pytest.raises(SystemError):
        temp_rpc.launch("anvil", port=temp_port)


def test_kill(temp_rpc):
    temp_rpc.kill()
    with pytest.raises(SystemError):
        temp_rpc.kill()
    temp_rpc.kill(False)
