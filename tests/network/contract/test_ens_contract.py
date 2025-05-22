#!/usr/bin/python3

import eth_retry
import pytest
from ens.exceptions import InvalidName

from brownie.exceptions import UnsetENSName
from brownie.network.contract import Contract


@eth_retry.auto_retry
def test_lookup(connect_to_mainnet):
    c = Contract.from_abi("Test", "ens.snakecharmers.eth", [])
    assert c == "0x808B53bF4D70A24bA5cb720D37A4835621A9df00"
    assert c == "ens.snakecharmers.eth"


@eth_retry.auto_retry
def test_invalid(connect_to_mainnet):
    with pytest.raises(InvalidName):
        Contract.from_abi("Test", "this-is-not-an-ENS-address,isit?.eth", [])


@eth_retry.auto_retry
def test_unset(connect_to_mainnet):
    with pytest.raises(UnsetENSName):
        Contract.from_abi("Test", "pleasedonot.buythisoryouwill.breakmytests.eth", [])
