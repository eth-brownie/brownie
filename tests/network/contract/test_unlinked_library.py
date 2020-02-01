#!/usr/bin/python3

import pytest

from brownie.exceptions import UndeployedLibrary
from brownie.network.contract import ProjectContract


def test_library_is_project_contract(accounts, librarytester):
    lib = accounts[0].deploy(librarytester["TestLib"])
    assert type(lib) is ProjectContract


def test_unlinked_library(accounts, librarytester):
    with pytest.raises(UndeployedLibrary):
        accounts[0].deploy(librarytester["Unlinked"])
    lib = accounts[0].deploy(librarytester["TestLib"])
    contract = accounts[0].deploy(librarytester["Unlinked"])
    assert lib.address[2:].lower() in contract.bytecode


def test_multiple_projects(accounts, librarytester, librarytester2):
    lib = accounts[0].deploy(librarytester["TestLib"])
    with pytest.raises(UndeployedLibrary):
        accounts[0].deploy(librarytester2["Unlinked"])
    lib2 = accounts[0].deploy(librarytester2["TestLib"])
    contract = accounts[0].deploy(librarytester["Unlinked"])
    assert lib.address[2:].lower() in contract.bytecode
    assert lib2.address[2:].lower() not in contract.bytecode
