#!/usr/bin/python3

import pytest

from brownie import compile_source
from brownie.exceptions import VirtualMachineError
from brownie.network.contract import ProjectContract
from brownie.network.transaction import TransactionReceipt


def test_returns_contract_on_success(BrownieTester, accounts):
    """returns a Contract instance on successful deployment"""
    c = accounts[0].deploy(BrownieTester, True)
    assert type(c) == ProjectContract


def test_raises_on_revert(BrownieTester, accounts):
    """raises on revert if not in console"""
    with pytest.raises(VirtualMachineError):
        accounts[0].deploy(BrownieTester, False)


def test_returns_tx_on_revert_in_console(BrownieTester, accounts, console_mode):
    """returns a TransactionReceipt instance on revert in the console"""
    tx = accounts[0].deploy(BrownieTester, False)
    assert type(tx) == TransactionReceipt
    assert tx.status == 0


def test_nonce(BrownieTester, accounts, chain):
    """nonces increment properly"""
    assert accounts[0].nonce == 0
    accounts[0].deploy(BrownieTester, True)
    assert accounts[0].nonce == 1
    chain.reset()
    assert accounts[0].nonce == 0


def test_gas_price_manual(BrownieTester, accounts):
    """gas price is set correctly when specified in the call"""
    balance = accounts[0].balance()
    tx = accounts[0].deploy(BrownieTester, True, gas_price=100).tx
    assert tx.gas_price == 100
    assert accounts[0].balance() == balance - (tx.gas_used * 100)


@pytest.mark.parametrize("auto", (True, False, None, "auto"))
def test_gas_price_automatic(BrownieTester, accounts, config, web3, auto):
    """gas price is set correctly using web3.eth.gas_price"""
    config.active_network["settings"]["gas_price"] = auto
    balance = accounts[0].balance()
    tx = accounts[0].deploy(BrownieTester, True).tx
    assert tx.gas_price == web3.eth.gas_price
    assert accounts[0].balance() == balance - (tx.gas_price * tx.gas_used)


def test_gas_price_config(BrownieTester, accounts, config, web3):
    """gas price is set correctly from the config"""
    config.active_network["settings"]["gas_price"] = 50
    balance = accounts[0].balance()
    tx = accounts[0].deploy(BrownieTester, True).tx
    assert tx.gas_price == 50
    assert accounts[0].balance() == balance - (50 * tx.gas_used)


def test_gas_price_zero(BrownieTester, accounts, config, web3):
    """gas price is set correctly from the config"""
    config.active_network["settings"]["gas_price"] = 0
    balance = accounts[0].balance()
    tx = accounts[0].deploy(BrownieTester, True).tx
    assert tx.gas_price == 0
    assert accounts[0].balance() == balance


def test_gas_limit_manual(BrownieTester, accounts):
    """gas limit is set correctly when specified in the call"""
    tx = accounts[0].deploy(BrownieTester, True, gas_limit=3000000).tx
    assert tx.gas_limit == 3000000


@pytest.mark.parametrize("auto", (True, False, None, "auto"))
def test_gas_limit_automatic(BrownieTester, accounts, config, auto):
    """gas limit is set correctly using web3.eth.estimate_gas"""
    config.active_network["settings"]["gas_limit"] = auto
    tx = accounts[0].deploy(BrownieTester, True).tx
    assert tx.gas_limit == tx.gas_used


def test_gas_limit_config(BrownieTester, accounts, config):
    """gas limit is set correctly from the config"""
    config.active_network["settings"]["gas_limit"] = 5000000
    tx = accounts[0].deploy(BrownieTester, True).tx
    assert tx.gas_limit == 5000000


def test_nonce_manual(BrownieTester, accounts):
    """returns a Contract instance on successful deployment with the correct nonce"""
    assert accounts[0].nonce == 0
    c = accounts[0].deploy(BrownieTester, True, nonce=0)
    assert type(c) == ProjectContract
    assert accounts[0].nonce == 1
    c = accounts[0].deploy(BrownieTester, True, nonce=1)
    assert type(c) == ProjectContract


def test_nonce_manual_on_revert_in_console(BrownieTester, accounts, console_mode):
    """returns a TransactionReceipt instance on reverted deployment with the correct nonce"""
    accounts[0].transfer(accounts[1], "1 ether")
    assert accounts[0].nonce == 1
    tx = accounts[0].deploy(BrownieTester, False, nonce=1)
    assert tx.nonce == 1


# this behaviour changed in ganache7, if the test suite is updated to work
# in hardhat we should still include it

# @pytest.mark.parametrize("nonce", (1, -1, 15))
# def test_raises_on_wrong_nonce(BrownieTester, accounts, nonce):
#     """raises if invalid manual nonce is provided"""
#     assert accounts[0].nonce == 0
#     with pytest.raises(ValueError):
#         accounts[0].deploy(BrownieTester, True, nonce=nonce)


def test_selfdestruct_during_deploy(accounts):
    foo = compile_source(
        """
pragma solidity 0.5.0;

contract Foo {
    constructor () public { selfdestruct(address(0)); }
}
    """
    ).Foo

    result = foo.deploy({"from": accounts[0]})
    assert isinstance(result, TransactionReceipt)
