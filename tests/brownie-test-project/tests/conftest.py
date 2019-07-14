#!/usr/bin/python3

import pytest

from brownie import accounts


@pytest.fixture(autouse=True)
def isolation(test_isolation):
    pass


@pytest.fixture(scope="module")
def token(Token):
    t = accounts[0].deploy(Token, "Test Token", "TEST", 18, "1000 ether")
    yield t
