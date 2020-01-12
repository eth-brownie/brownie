#!/usr/bin/python3

import pytest

# from brownie import network, accounts, config, web3
from brownie.exceptions import VirtualMachineError
from brownie.network.transaction import TransactionReceipt


def test_to_string(accounts):
    """Can send to a string"""
    tx = accounts[0].transfer("0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E", 10000)
    assert tx.receiver == "0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E"


def test_to_account(accounts):
    """Can send to an Account object"""
    tx = accounts[0].transfer(accounts[1], 10000)
    assert str(tx.receiver) == accounts[1].address


def test_to_contract(accounts, tester):
    """Can send to a Contract object"""
    tx = accounts[0].transfer(tester, 0, data=tester.signatures["doNothing"])
    assert str(tx.receiver) == tester.address
    assert tx.gas_used > 21000


def test_to_contract_fallback(accounts, tester):
    tx = accounts[0].transfer(tester, "1 ether")
    assert str(tx.receiver) == tester.address
    assert tx.gas_used > 21000


def test_returns_tx_on_success(accounts):
    """returns a TransactionReceipt on success"""
    tx = accounts[0].transfer(accounts[1], 1000)
    assert type(tx) == TransactionReceipt


def test_raises_on_revert(accounts, tester):
    """raises on revert"""
    with pytest.raises(VirtualMachineError):
        accounts[0].transfer(tester, 0)


def test_returns_tx_on_revert_in_console(accounts, tester, console_mode):
    """returns a tx on revert in console"""
    tx = accounts[0].transfer(tester, 0)
    assert type(tx) == TransactionReceipt
    assert tx.status == 0


def test_broadcast_revert(accounts, tester, config):
    config["active_network"]["reverting_tx_gas_limit"] = False
    assert accounts[1].nonce == 0
    with pytest.raises(VirtualMachineError):
        accounts[1].transfer(tester, 0)
    assert accounts[1].nonce == 0
    config["active_network"]["reverting_tx_gas_limit"] = 1000000
    with pytest.raises(VirtualMachineError):
        accounts[1].transfer(tester, 0)
    assert accounts[1].nonce == 1


def test_nonce(accounts):
    """nonces increment properly"""
    assert accounts[1].nonce == 0
    accounts[1].transfer(accounts[2], 1000)
    assert accounts[2].nonce == 0
    assert accounts[1].nonce == 1


def test_balance_int(accounts, web3, rpc):
    """transfers use the correct balance"""
    balance = accounts[0].balance()
    assert web3.eth.getBalance(accounts[0].address) == balance
    accounts[1].transfer(accounts[0], 1000)
    assert accounts[0].balance() == balance + 1000
    rpc.reset()
    assert web3.eth.getBalance(accounts[0].address) == balance


def test_balance_wei(accounts, web3, rpc):
    """transfer balances are converted using wei"""
    balance = accounts[0].balance()
    assert web3.eth.getBalance(accounts[0].address) == balance
    accounts[1].transfer(accounts[0], "1 ether")
    assert accounts[0].balance() == balance + 1000000000000000000
    rpc.reset()
    assert web3.eth.getBalance(accounts[0].address) == balance


def test_gas_price_manual(accounts):
    """gas price is set correctly when specified in the call"""
    balance = accounts[0].balance()
    tx = accounts[0].transfer(accounts[1], 0, gas_price=100)
    assert tx.gas_price == 100
    assert accounts[0].balance() == balance - (100 * 21000)


@pytest.mark.parametrize("auto", (True, False, None, "auto"))
def test_gas_price_automatic(accounts, config, web3, auto):
    """gas price is set correctly using web3.eth.gasPrice"""
    config["active_network"]["gas_price"] = auto
    balance = accounts[0].balance()
    tx = accounts[0].transfer(accounts[1], 0)
    assert tx.gas_price == web3.eth.gasPrice
    assert accounts[0].balance() == balance - (tx.gas_price * 21000)


def test_gas_price_config(accounts, config):
    """gas price is set correctly from the config"""
    config["active_network"]["gas_price"] = 50
    balance = accounts[0].balance()
    tx = accounts[0].transfer(accounts[1], 0)
    assert tx.gas_price == 50
    assert accounts[0].balance() == balance - (50 * 21000)


def test_gas_price_zero(accounts, config):
    config["active_network"]["gas_price"] = 0
    balance = accounts[0].balance()
    tx = accounts[0].transfer(accounts[1], 1337)
    assert tx.gas_price == 0
    assert accounts[0].balance() == balance - 1337


def test_gas_limit_manual(accounts):
    """gas limit is set correctly when specified in the call"""
    tx = accounts[0].transfer(accounts[1], 1000, gas_limit=100000)
    assert tx.gas_limit == 100000
    assert tx.gas_used == 21000


@pytest.mark.parametrize("auto", (True, False, None, "auto"))
def test_gas_limit_automatic(accounts, config, auto):
    """gas limit is set correctly using web3.eth.estimateGas"""
    config["active_network"]["gas_limit"] = auto
    tx = accounts[0].transfer(accounts[1], 1000)
    assert tx.gas_limit == 21000


def test_gas_limit_config(accounts, config):
    """gas limit is set correctly from the config"""
    config["active_network"]["gas_limit"] = 50000
    tx = accounts[0].transfer(accounts[1], 1000)
    assert tx.gas_limit == 50000
    assert tx.gas_used == 21000
    config["active_network"]["gas_limit"] = False


def test_data(accounts):
    """transaction data is set correctly"""
    tx = accounts[0].transfer(accounts[1], 1000)
    assert tx.input == "0x"
    tx = accounts[0].transfer(accounts[1], 1000, data="0x1234")
    assert tx.input == "0x1234"


def test_localaccount(accounts):
    local = accounts.add()
    assert local.balance() == 0
    accounts[0].transfer(local, "10 ether")
    assert local.balance() == "10 ether"
    local.transfer(accounts[1], "1 ether")
    assert accounts[1].balance() == "101 ether"
    assert local.nonce == 1
