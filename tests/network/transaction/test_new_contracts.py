#!/usr/bin/python3

import pytest

from brownie.network.contract import ProjectContract

solidity_source = """
pragma solidity 0.6.2;

contract Foo {

    constructor (bool _fail) public {
        require(!_fail);
    }

    function foo () public view returns (uint256) { return 42; }
}

contract Deployer {

    function create (bool _fail) public returns (Foo) {
        return new Foo(_fail);
    }

    function create2 (bool _fail) public returns (Foo) {
        bytes32 _salt = 0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef;
        return new Foo{salt: _salt}(_fail);
    }
}

"""


@pytest.fixture
def solcproject(newproject, accounts):
    with newproject._path.joinpath("contracts/Test.sol").open("w") as fp:
        fp.write(solidity_source)
    newproject.load()

    newproject.Deployer.deploy({"from": accounts[0]})
    yield newproject


def test_solidity_create(solcproject):
    deployer = solcproject.Deployer[0]
    tx = deployer.create(False)

    tx.call_trace()
    assert len(tx.new_contracts) == 1
    foo = solcproject.Foo.at(tx.new_contracts[0])
    assert type(foo) is ProjectContract
    assert foo.foo() == 42


def test_solidity_create2(solcproject):
    deployer = solcproject.Deployer[0]
    tx = deployer.create2(False)

    tx.call_trace()
    assert len(tx.new_contracts) == 1
    foo = solcproject.Foo.at(tx.new_contracts[0])
    assert type(foo) is ProjectContract
    assert foo.foo() == 42


def test_solidity_reverts(solcproject, console_mode):
    deployer = solcproject.Deployer[0]
    tx = deployer.create(True)

    tx.call_trace()
    assert len(tx.new_contracts) == 0


vyper_forwarder_source = """
# @version 0.2.4
@external
def create_new(_target: address) -> address:
    return create_forwarder_to(_target)
"""

vyper_factory_source = """
# @version 0.2.4
@external
@view
def foo() -> uint256:
    return 42
"""


def test_vyper_create_forwarder_to(newproject, accounts):
    with newproject._path.joinpath("contracts/Forwarder.vy").open("w") as fp:
        fp.write(vyper_forwarder_source)
    with newproject._path.joinpath("contracts/Foo.vy").open("w") as fp:
        fp.write(vyper_factory_source)
    newproject.load()

    foo = newproject.Foo.deploy({"from": accounts[0]})
    forwarder = newproject.Forwarder.deploy({"from": accounts[0]})
    tx = forwarder.create_new(foo)

    assert len(tx.new_contracts) == 1
    foo2 = newproject.Foo.at(tx.new_contracts[0])

    assert "pcMap" in foo._build

    assert type(foo2) is ProjectContract
    assert "pcMap" not in foo2._build
    assert foo2.foo() == 42
