#!/usr/bin/python3

import pytest

from brownie import rpc
from brownie.exceptions import RPCProcessError


def test_launch_file_not_found(no_rpc):
    with pytest.raises(FileNotFoundError):
        rpc.launch("not-ganache")


def test_launch_process_fails(no_rpc):
    with pytest.raises(RPCProcessError):
        rpc.launch("ganache-cli --help")


def test_launch(no_rpc):
    assert not rpc.is_active()
    assert not rpc.is_child()
    rpc.launch("ganache-cli")
    assert rpc.is_active()
    assert rpc.is_child()


def test_already_active(no_rpc):
    with pytest.raises(SystemError):
        rpc.launch("ganache-cli")


def test_kill(no_rpc):
    rpc.kill()
    with pytest.raises(SystemError):
        rpc.kill()
    rpc.kill(False)
