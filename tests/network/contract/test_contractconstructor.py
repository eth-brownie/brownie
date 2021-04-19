#!/usr/bin/python3

import pytest

from brownie.exceptions import VirtualMachineError
from brownie.network.contract import ProjectContract
from brownie.network.transaction import TransactionReceipt


def test_returns_contract_on_success(BrownieTester, accounts):
    """returns a Contract instance on successful deployment"""
    c = BrownieTester.deploy(True, {"from": accounts[0]})
    assert type(c) == ProjectContract


def test_raises_on_revert(BrownieTester, accounts):
    """raises on revert if not in console"""
    with pytest.raises(VirtualMachineError):
        BrownieTester.deploy(False, {"from": accounts[0]})


def test_returns_tx_on_revert_in_console(BrownieTester, accounts, console_mode):
    """returns a TransactionReceipt instance on revert in the console"""
    tx = BrownieTester.deploy(False, {"from": accounts[0]})
    assert type(tx) == TransactionReceipt
    assert tx.status == 0


def test_nonce(BrownieTester, accounts, chain):
    """nonces increment properly"""
    assert accounts[0].nonce == 0
    BrownieTester.deploy(True, {"from": accounts[0]})
    assert accounts[0].nonce == 1
    chain.reset()
    assert accounts[0].nonce == 0


def test_gas_price_manual(BrownieTester, accounts):
    """gas price is set correctly when specified in the call"""
    balance = accounts[0].balance()
    tx = BrownieTester.deploy(True, {"from": accounts[0], "gas_price": 100}).tx
    assert tx.gas_price == 100
    assert accounts[0].balance() == balance - (tx.gas_used * 100)


@pytest.mark.parametrize("auto", (True, False, None, "auto"))
def test_gas_price_automatic(BrownieTester, accounts, config, web3, auto):
    """gas price is set correctly using web3.eth.gas_price"""
    config.active_network["settings"]["gas_price"] = auto
    balance = accounts[0].balance()
    tx = BrownieTester.deploy(True, {"from": accounts[0]}).tx
    assert tx.gas_price == web3.eth.gas_price
    assert accounts[0].balance() == balance - (tx.gas_price * tx.gas_used)


def test_gas_price_config(BrownieTester, accounts, config):
    """gas price is set correctly from the config"""
    config.active_network["settings"]["gas_price"] = 50
    balance = accounts[0].balance()
    tx = BrownieTester.deploy(True, {"from": accounts[0]}).tx
    assert tx.gas_price == 50
    assert accounts[0].balance() == balance - (50 * tx.gas_used)


def test_gas_limit_manual(BrownieTester, accounts):
    """gas limit is set correctly when specified in the call"""
    tx = BrownieTester.deploy(True, {"from": accounts[0], "gas_limit": 3000000}).tx
    assert tx.gas_limit == 3000000


@pytest.mark.parametrize("auto", (True, False, None, "auto"))
def test_gas_limit_automatic(BrownieTester, accounts, config, auto):
    """gas limit is set correctly using web3.eth.estimate_gas"""
    config.active_network["settings"]["gas_limit"] = auto
    tx = BrownieTester.deploy(True, {"from": accounts[0]}).tx
    assert tx.gas_limit == tx.gas_used


def test_gas_limit_config(BrownieTester, accounts, config):
    """gas limit is set correctly from the config"""
    config.active_network["settings"]["gas_limit"] = 5000000
    tx = BrownieTester.deploy(True, {"from": accounts[0]}).tx
    assert tx.gas_limit == 5000000
    config.active_network["settings"]["gas_limit"] = False


def test_repr(BrownieTester, accounts):
    repr(BrownieTester)
    repr(BrownieTester.deploy)
