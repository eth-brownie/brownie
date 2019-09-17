#!/usr/bin/python3

import pytest

from brownie import config, rpc, web3
from brownie.network.rpc import _notify_registry


def _launch(cmd):
    if "-p " not in cmd:
        cmd += " -p 31337"
    rpc._launch(cmd)


@pytest.fixture(scope="module")
def no_rpc():
    config._unlock()
    config["network"]["networks"]["development"]["host"] = "http://127.0.0.1:31337"
    web3.connect("http://127.0.0.1:31337")
    proc = rpc._rpc
    reset_id = rpc._reset_id
    rpc._rpc = None
    rpc._reset_id = False
    rpc._launch = rpc.launch
    rpc.launch = _launch
    _notify_registry(0)
    yield
    config["network"]["networks"]["development"]["host"] = "http://127.0.0.1:8545"
    web3.connect("http://127.0.0.1:8545")
    rpc.launch = rpc._launch
    rpc.kill(False)
    _notify_registry(0)
    rpc._rpc = proc
    rpc._reset_id = reset_id
