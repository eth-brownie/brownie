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


@pytest.fixture(scope="session")
def temp_host(xdist_id):
    return "127.0.0.2"


@pytest.fixture(scope="session")
def original_host():
    return "127.0.0.1"


@pytest.fixture(scope="module")
def _no_rpc_setup(
    rpc, chain, web3, temp_port, original_port, temp_host, original_host, network_name
):
    CONFIG.networks[network_name]["cmd_settings"]["port"] = temp_port
    CONFIG.networks[network_name]["host"] = f"http://{temp_host}"
    web3.connect(f"http://{temp_host}:{temp_port}")
    proc = rpc.process
    reset_id = chain._reset_id
    rpc.process = None
    chain._reset_id = False
    # rpc._launch = rpc.launch
    # rpc.launch = _launch
    _notify_registry(0)
    yield
    CONFIG.networks[network_name]["cmd_settings"]["port"] = original_port
    # CONFIG.networks[network_name]["host"] = temp_host
    web3.connect(f"http://{original_host}:{original_port}")
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
def temp_rpc(no_rpc, temp_port, temp_host):
    if not no_rpc.process or not no_rpc.is_active():
        no_rpc.launch("ganache-cli", port=temp_port, host=temp_host)
    yield no_rpc
