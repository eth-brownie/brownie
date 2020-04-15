#!/usr/bin/python3

import pytest
from ens.exceptions import InvalidName

from brownie.exceptions import UnsetENSName
from brownie.network.contract import Contract


def test_lookup(network):
    network.connect("mainnet")
    c = Contract.from_abi("Test", "ens.snakecharmers.eth", [])
    assert c == "0x808B53bF4D70A24bA5cb720D37A4835621A9df00"
    assert c == "ens.snakecharmers.eth"


def test_invalid(network):
    network.connect("mainnet")
    with pytest.raises(InvalidName):
        Contract.from_abi("Test", "this-is-not-an-ENS-address,isit?.eth", [])


def test_unset(network):
    network.connect("mainnet")
    with pytest.raises(UnsetENSName):
        Contract.from_abi("Test", "pleasedonot.buythisoryouwill.breakmytests.eth", [])
