#!/usr/bin/python3

import pytest
from ens.exceptions import InvalidName

from brownie.exceptions import UnsetENSName
from brownie.network.account import PublicKeyAccount

ENS_ADDRESS = "0x808B53bF4D70A24bA5cb720D37A4835621A9df00"
ENS_DOMAIN = "ens.snakecharmers.eth"
UNSET_ENS_DOMAIN = "pleasedonot.buythisoryouwill.breakmytests.eth"


def test_lookup(fake_ens):
    fake_ens({ENS_DOMAIN: ENS_ADDRESS})

    pub = PublicKeyAccount("ens.snakecharmers.eth")
    assert pub == ENS_ADDRESS
    assert pub == ENS_DOMAIN


def test_invalid(fake_ens):
    fake_ens({"this-is-not-an-ens-address,isit?.eth": InvalidName("Invalid ENS name")})

    with pytest.raises(InvalidName):
        PublicKeyAccount("this-is-not-an-ENS-address,isit?.eth")


def test_unset(fake_ens):
    fake_ens({UNSET_ENS_DOMAIN: None})

    with pytest.raises(UnsetENSName):
        PublicKeyAccount(UNSET_ENS_DOMAIN)
