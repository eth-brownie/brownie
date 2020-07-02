#!/usr/bin/python3

import pytest

from brownie.network.contract import ContractCall, ContractTx, OverloadedMethod
from brownie.project import compile_source

vyper_source = """
@external
@view
def foo(a: int128, b: int128 = 42) -> int128:
    return a + b
"""

solidity_source = """
pragma solidity ^0.5.0;

contract OverloadedTester {
    function foo(uint256 a) public view returns (bool) { return true; }
    function foo(bool a) public returns (bool) { return a; }
    function foo(uint256 a, uint256 b) public view returns (uint256) { return a+b; }
}
"""


@pytest.fixture
def vyper_tester(accounts):
    container = compile_source(vyper_source).Vyper
    yield container.deploy({"from": accounts[0]})


@pytest.fixture
def solc_tester(accounts):
    container = compile_source(solidity_source).OverloadedTester
    yield container.deploy({"from": accounts[0]})


def test_objects(solc_tester):
    assert isinstance(solc_tester.foo, OverloadedMethod)
    assert len(solc_tester.foo) == 3
    assert isinstance(solc_tester.foo.methods[("uint",)], ContractCall)
    assert isinstance(solc_tester.foo.methods[("bool",)], ContractTx)


def test_keys(solc_tester):
    assert solc_tester.foo["uint"] == solc_tester.foo["uint256"]
    assert solc_tester.foo["uint", "uint"] == solc_tester.foo["uint256, uint256"]
    assert solc_tester.foo["uint"] != solc_tester.foo["bool"]


def test_forwarding_methods(solc_tester):
    foo = solc_tester.foo

    assert foo(12, 13) == foo["uint,uint"](12, 13)
    assert foo.call(12, 13) == foo["uint,uint"].call(12, 13)
    assert foo.transact(12, 13).return_value == foo["uint,uint"].transact(12, 13).return_value
    assert foo.encode_input(12, 13) == foo["uint,uint"].encode_input(12, 13)


def test_call_raises(accounts, solc_tester):
    with pytest.raises(ValueError):
        solc_tester.foo()
    with pytest.raises(ValueError):
        solc_tester.foo(1)

    # including a tx params dictionary should not affect the outcome
    with pytest.raises(ValueError):
        solc_tester.foo({"from": accounts[0]})
    with pytest.raises(ValueError):
        solc_tester.foo(1, {"from": accounts[0]})


def test_vyper(vyper_tester):
    assert isinstance(vyper_tester.foo, OverloadedMethod)
    assert len(vyper_tester.foo) == 2

    assert vyper_tester.foo(1) == 43
    assert vyper_tester.foo(2, 2) == 4
