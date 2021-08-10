#!/usr/bin/python3

import pytest

from brownie._config import CONFIG
from brownie.network.state import _notify_registry


@pytest.fixture(scope="session")
def temp_port(xdist_id):
    return 31337 + xdist_id


@pytest.fixture(scope="session")
def original_port(xdist_id):
    return 8545 + xdist_id


@pytest.fixture(scope="module")
def _no_rpc_setup(rpc, chain, web3, temp_port, original_port, network_name):
    CONFIG.networks[network_name]["cmd_settings"]["port"] = temp_port
    web3.connect(f"http://127.0.0.1:{temp_port}")
    proc = rpc.process
    reset_id = chain._reset_id
    rpc.process = None
    chain._reset_id = False
    # rpc._launch = rpc.launch
    # rpc.launch = _launch
    _notify_registry(0)
    yield
    CONFIG.networks[network_name]["cmd_settings"]["port"] = original_port
    web3.connect(f"http://127.0.0.1:{original_port}")
    # rpc.launch = rpc._launch
    rpc.kill(False)
    _notify_registry(0)
    rpc.process = proc
    chain._reset_id = reset_id
    chain._current_id = reset_id


@pytest.fixture
def no_rpc(_no_rpc_setup, rpc):
    yield rpc


@pytest.fixture
def temp_rpc(no_rpc, temp_port):
    if not no_rpc.process or not no_rpc.is_active():
        no_rpc.launch("ganache-cli", port=temp_port)
    yield no_rpc
