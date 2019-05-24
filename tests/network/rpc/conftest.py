#!/usr/bin/python3

import pytest

from brownie import rpc


@pytest.fixture(scope="module")
def no_rpc():
    rpc.kill(False)
    yield
    if not rpc.is_active():
        rpc.launch('ganache-cli')
