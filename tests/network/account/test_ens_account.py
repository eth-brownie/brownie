#!/usr/bin/python3

import pytest
from ens.exceptions import InvalidName

from brownie.exceptions import UnsetENSName
from brownie.network.account import PublicKeyAccount


def test_lookup():
    pub = PublicKeyAccount("ens.snakecharmers.eth")
    assert pub == "0x808B53bF4D70A24bA5cb720D37A4835621A9df00"
    assert pub == "ens.snakecharmers.eth"


def test_invalid():
    with pytest.raises(InvalidName):
        PublicKeyAccount("this-is-not-an-ENS-address,isit?.eth")


def test_unset():
    with pytest.raises(UnsetENSName):
        PublicKeyAccount("pleasedonot.buythisoryouwill.breakmytests.eth")
