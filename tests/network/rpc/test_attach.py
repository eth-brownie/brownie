#!/usr/bin/python3

import pytest

from brownie import rpc


def test_attach_lookup_error(no_rpc):
    with pytest.raises(ProcessLookupError):
        rpc.attach("http://127.0.0.1:7545")


def test_already_active(no_rpc):
    rpc.launch("ganache-cli -a 20")
    with pytest.raises(SystemError):
        rpc.attach("http://127.0.0.1:31337")


def test_attach(no_rpc):
    rpc._rpc = None
    rpc.attach("http://127.0.0.1:31337")
    rpc._rpc = None
    rpc.attach(("127.0.0.1", 31337))
    assert rpc.is_active()


# coverage doesn't like killing the attached process
def test_kill(no_rpc):
    rpc.kill()
    with pytest.raises(SystemError):
        rpc.kill()
    rpc.kill(False)
