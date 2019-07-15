#!/usr/bin/python3

import pytest

from brownie import accounts, web3


@pytest.fixture(autouse=True)
def isolation(module_isolation):
    pass


@pytest.fixture(scope="module", autouse=True)
def setup():
    accounts[0].transfer(accounts[1], "1 ether")


def test_isolation_first():
    assert web3.eth.blockNumber == 1
    assert accounts[1].balance() == "101 ether"
    accounts[0].transfer(accounts[1], "1 ether")


def test_isolation_second():
    assert web3.eth.blockNumber == 2
    assert accounts[1].balance() == "102 ether"
