#!/usr/bin/python3

import pytest

from brownie.exceptions import UndeployedLibrary


def test_unlinked_library(accounts, librarytester):
    with pytest.raises(UndeployedLibrary):
        accounts[0].deploy(librarytester['Unlinked'])
    lib = accounts[0].deploy(librarytester['TestLib'])
    contract = accounts[0].deploy(librarytester['Unlinked'])
    assert lib.address[2:].lower() in contract.bytecode
