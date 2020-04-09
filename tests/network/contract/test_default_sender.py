import pytest

from brownie.project import compile_source

TEST_SOURCE = """
pragma solidity ^0.6.0;

contract Foo {
    constructor () public {}
    function bar() public {}
}
"""


@pytest.fixture
def Foo():
    yield compile_source(TEST_SOURCE).Foo


def test_cli_no_owner(Foo, accounts, test_mode, config):
    config.active_network["settings"]["default_contract_owner"] = False
    foo = Foo.deploy({"from": accounts[0]})

    with pytest.raises(AttributeError):
        foo.bar()


def test_without_from_sends_from_deployer(Foo, accounts):
    foo = Foo.deploy({"from": accounts[0]})
    tx = foo.bar()

    assert tx.sender == accounts[0]


def test_deploy_with_default_account(Foo, accounts):
    accounts.default = accounts[1]
    foo = Foo.deploy()

    assert foo.tx.sender == accounts[1]


def test_deploy_without_default_account(Foo, accounts):
    assert accounts.default is None
    with pytest.raises(AttributeError):
        Foo.deploy()


def test_contract_owner_overrides_default_account(Foo, accounts):
    accounts.default = accounts[1]
    foo = Foo.deploy({"from": accounts[2]})
    tx = foo.bar()

    assert tx.sender == accounts[2]
