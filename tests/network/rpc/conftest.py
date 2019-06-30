#!/usr/bin/python3

import pytest

from brownie import rpc, config, web3


def _launch(cmd):
    rpc._launch(cmd+" -p 31337")


@pytest.fixture(scope="module")
def no_rpc():
    config._unlock()
    config['networks']['development']['host'] = "http://127.0.0.1:31337"
    web3.connect("http://127.0.0.1:31337")
    proc = rpc._rpc
    reset_id = rpc._reset_id
    rpc._rpc = None
    rpc._reset_id = False
    rpc._launch = rpc.launch
    rpc.launch = _launch
    rpc._reset()
    yield
    config['networks']['development']['host'] = "http://127.0.0.1:8545"
    web3.connect("http://127.0.0.1:8545")
    rpc.launch = rpc._launch
    rpc.kill(False)
    rpc._reset()
    rpc._rpc = proc
    rpc._reset_id = reset_id
