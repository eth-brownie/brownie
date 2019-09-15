#!/usr/bin/python3

from copy import deepcopy
import pytest

from brownie import Wei
from brownie.network.contract import (
    _DeployedContractBase,
    Contract,
    ContractCall,
    ContractTx,
    OverloadedMethod,
    ProjectContract,
)
from brownie.exceptions import ContractExists, ContractNotFound


@pytest.fixture
def build(testproject):
    build = testproject._build.get("BrownieTester")
    yield deepcopy(build)


def test_type(tester):
    assert type(tester) is ProjectContract
    assert isinstance(tester, _DeployedContractBase)


def test_namespace_collision(tester, build):
    build["abi"].append(
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"},
                {"name": "_test", "type": "uint256"},
            ],
            "name": "bytecode",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        }
    )
    with pytest.raises(AttributeError):
        Contract(tester.address, None, build["abi"])


def test_overloaded(testproject, tester, build):
    build["abi"].append(
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"},
                {"name": "_test", "type": "uint256"},
            ],
            "name": "revertStrings",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        }
    )
    del testproject.BrownieTester[0]
    c = Contract(tester.address, None, build["abi"])
    fn = c.revertStrings
    assert type(fn) == OverloadedMethod
    assert len(fn) == 2
    assert type(fn["uint"]) == ContractTx
    assert fn["address", "uint256", "uint256"] == fn["address, uint256, uint256"]
    assert fn["uint"] == fn["uint256"]
    assert fn["uint"] != fn["address, uint256, uint256"]
    repr(fn)


def test_set_methods(tester):
    for item in tester.abi:
        if item["type"] != "function":
            if "name" not in item:
                continue
            assert not hasattr(tester, item["name"])
        elif item["stateMutability"] in ("view", "pure"):
            assert type(getattr(tester, item["name"])) == ContractCall
        else:
            assert type(getattr(tester, item["name"])) == ContractTx


def test_balance(tester):
    balance = tester.balance()
    assert type(balance) is Wei
    assert balance == "0 ether"


def test_comparison(testproject, tester):
    del testproject.BrownieTester[0]
    assert tester != 123
    assert tester == str(tester.address)
    assert tester == Contract(tester.address, "BrownieTester", tester.abi)
    repr(tester)


def test_revert_not_found(tester, rpc):
    rpc.reset()
    with pytest.raises(ContractNotFound):
        tester.balance()


def test_contractabi_replace_contract(testproject, tester):
    with pytest.raises(ContractExists):
        Contract(tester.address, "BrownieTester", tester.abi)
    del testproject.BrownieTester[0]
    Contract(tester.address, "BrownieTester", tester.abi)
    Contract(tester.address, "BrownieTester", tester.abi)
