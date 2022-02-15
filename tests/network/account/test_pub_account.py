#!/usr/bin/python3

import pytest

from brownie import Wei
from brownie.network.account import PublicKeyAccount


def test_init(accounts):
    PublicKeyAccount("0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E")
    PublicKeyAccount(accounts[0])
    with pytest.raises(ValueError):
        PublicKeyAccount("0x416b8a7d9290502f5661da81f0cf43893e3d19cb9aea3c426cfb36e8186e9c09")


def test_eq(accounts):
    pub = PublicKeyAccount("0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E")
    assert pub == PublicKeyAccount("0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E")
    assert pub == "0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E"
    assert pub != "potato"
    assert PublicKeyAccount(accounts[0]) == accounts[0]


def test_balance(accounts):
    balance = PublicKeyAccount(accounts[0]).balance()
    assert isinstance(balance, Wei)
    assert balance == "1000 ether"


def test_transfer(accounts, chain):
    pub = PublicKeyAccount("0x0000Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E")
    assert pub.balance() == 0
    accounts[0].transfer(pub, "10 ether")
    assert pub.balance() == "10 ether"
    chain.reset()
    assert pub.balance() == 0
