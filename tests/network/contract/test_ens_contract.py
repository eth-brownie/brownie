#!/usr/bin/python3

import pytest
from ens.exceptions import InvalidName
from hexbytes import HexBytes

from brownie.exceptions import UnsetENSName
from brownie.network.contract import Contract
from brownie.network.web3 import web3

ENS_ADDRESS = "0x808B53bF4D70A24bA5cb720D37A4835621A9df00"
ENS_DOMAIN = "ens.snakecharmers.eth"
UNSET_ENS_DOMAIN = "pleasedonot.buythisoryouwill.breakmytests.eth"


def test_lookup(fake_ens, monkeypatch):
    fake_ens({ENS_DOMAIN: ENS_ADDRESS})
    monkeypatch.setattr(web3.eth, "get_code", lambda address: HexBytes("0x6000"))

    c = Contract.from_abi("Test", ENS_DOMAIN, [], persist=False)
    assert c == ENS_ADDRESS
    assert c == ENS_DOMAIN


def test_invalid(fake_ens):
    fake_ens({"this-is-not-an-ens-address,isit?.eth": InvalidName("Invalid ENS name")})

    with pytest.raises(InvalidName):
        Contract.from_abi("Test", "this-is-not-an-ENS-address,isit?.eth", [])


def test_unset(fake_ens):
    fake_ens({UNSET_ENS_DOMAIN: None})

    with pytest.raises(UnsetENSName):
        Contract.from_abi("Test", UNSET_ENS_DOMAIN, [])
