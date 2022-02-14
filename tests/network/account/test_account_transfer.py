#!/usr/bin/python3

import pytest

from brownie import compile_source
from brownie.exceptions import VirtualMachineError
from brownie.network.transaction import TransactionReceipt

code = """
pragma solidity ^0.6.0;
contract Foo {
    fallback () external payable {}
}
"""


def test_to_string(accounts):
    """Can send to a string"""
    tx = accounts[0].transfer("0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E", 10000)
    assert tx.receiver == "0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E"


def test_to_string_without_checksum(accounts):
    to = "0x14b0Ed2a7C4cC60DD8F676AE44D0831d3c9b2a9E".lower()
    tx = accounts[0].transfer(to, 10000)
    assert tx.receiver.lower() == to


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


def test_allow_revert(accounts, tester, config):
    with pytest.raises(VirtualMachineError):
        accounts[1].transfer(tester, 0)

    assert accounts[1].nonce == 1

    with pytest.raises(ValueError):
        accounts[1].transfer(tester, 0, allow_revert=False)

    assert accounts[1].nonce == 1


def test_nonce(accounts):
    """nonces increment properly"""
    assert accounts[1].nonce == 0
    accounts[1].transfer(accounts[2], 1000)
    assert accounts[2].nonce == 0
    assert accounts[1].nonce == 1


def test_balance_int(accounts, web3, chain):
    """transfers use the correct balance"""
    balance = accounts[0].balance()
    assert web3.eth.get_balance(accounts[0].address) == balance
    accounts[1].transfer(accounts[0], 1000)
    assert accounts[0].balance() == balance + 1000
    chain.reset()
    assert web3.eth.get_balance(accounts[0].address) == balance


def test_balance_wei(accounts, web3, chain):
    """transfer balances are converted using wei"""
    balance = accounts[0].balance()
    assert web3.eth.get_balance(accounts[0].address) == balance
    accounts[1].transfer(accounts[0], "1 ether")
    assert accounts[0].balance() == balance + 1000000000000000000
    chain.reset()
    assert web3.eth.get_balance(accounts[0].address) == balance


def test_gas_price_manual(accounts):
    """gas price is set correctly when specified in the call"""
    balance = accounts[0].balance()
    tx = accounts[0].transfer(accounts[1], 0, gas_price=100)
    assert tx.gas_price == 100
    assert accounts[0].balance() == balance - (100 * 21000)


@pytest.mark.parametrize("auto", (True, False, None, "auto"))
def test_gas_price_automatic(accounts, config, web3, auto):
    """gas price is set correctly using web3.eth.gas_price"""
    config.active_network["settings"]["gas_price"] = auto
    balance = accounts[0].balance()
    tx = accounts[0].transfer(accounts[1], 0)
    assert tx.gas_price == web3.eth.gas_price
    assert accounts[0].balance() == balance - (tx.gas_price * 21000)


def test_gas_price_config(accounts, config):
    """gas price is set correctly from the config"""
    config.active_network["settings"]["gas_price"] = 50
    balance = accounts[0].balance()
    tx = accounts[0].transfer(accounts[1], 0)
    assert tx.gas_price == 50
    assert accounts[0].balance() == balance - (50 * 21000)


def test_gas_price_zero(accounts, config):
    config.active_network["settings"]["gas_price"] = 0
    balance = accounts[0].balance()
    tx = accounts[0].transfer(accounts[1], 1337)
    assert tx.gas_price == 0
    assert accounts[0].balance() == balance - 1337


def test_gas_limit_manual(accounts):
    """gas limit is set correctly when specified in the call"""
    tx = accounts[0].transfer(accounts[1], 1000, gas_limit=100000)
    assert tx.gas_limit == 100000
    assert tx.gas_used == 21000


def test_gas_buffer_manual(accounts, config):
    """gas limit is set correctly when specified in the call"""
    config.active_network["settings"]["gas_limit"] = None
    foo = compile_source(code).Foo.deploy({"from": accounts[0]})
    tx = accounts[0].transfer(foo, 1000, gas_buffer=1.337)
    assert int(tx.gas_used * 1.337) == tx.gas_limit


def test_gas_buffer_send_to_eoa(accounts, config):
    """gas limit is set correctly when specified in the call"""
    config.active_network["settings"]["gas_limit"] = None
    tx = accounts[0].transfer(accounts[1], 1000, gas_buffer=1.337)
    assert tx.gas_limit == 21000


@pytest.mark.parametrize("gas_limit", (True, False, None, "auto"))
@pytest.mark.parametrize("gas_buffer", (1, 1.25))
def test_gas_limit_automatic(accounts, config, gas_limit, gas_buffer):
    """gas limit is set correctly using web3.eth.estimate_gas"""
    config.active_network["settings"]["gas_limit"] = gas_limit
    config.active_network["settings"]["gas_buffer"] = gas_buffer
    foo = compile_source(code).Foo.deploy({"from": accounts[0]})
    tx = accounts[0].transfer(foo, 1000)
    assert int(tx.gas_used * gas_buffer) == tx.gas_limit


def test_gas_limit_config(accounts, config):
    """gas limit is set correctly from the config"""
    config.active_network["settings"]["gas_limit"] = 50000
    tx = accounts[0].transfer(accounts[1], 1000)
    assert tx.gas_limit == 50000
    assert tx.gas_used == 21000
    config.active_network["settings"]["gas_limit"] = False


def test_nonce_manual(accounts):
    """returns a Contract instance on successful deployment with the correct nonce"""
    assert accounts[0].nonce == 0
    tx = accounts[0].transfer(accounts[1], 1000, nonce=0)
    assert tx.nonce == 0
    assert accounts[0].nonce == 1
    tx = accounts[0].transfer(accounts[1], 1000, nonce=1)
    assert tx.nonce == 1


# this behaviour changed in ganache7, if the test suite is updated to work
# in hardhat we should still include it

# @pytest.mark.parametrize("nonce", (1, -1, 15))
# def test_raises_on_wrong_nonce(accounts, nonce):
#     """raises if invalid manual nonce is provided"""
#     assert accounts[0].nonce == 0
#     with pytest.raises(ValueError):
#         accounts[0].transfer(accounts[1], 1000, nonce=nonce)


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
    assert accounts[1].balance() == "1001 ether"
    assert local.nonce == 1


def test_deploy_via_transfer(accounts, web3):
    bytecode = "0x3660006000376110006000366000732157a7894439191e520825fe9399ab8655e0f7085af41558576110006000f3"  # NOQA: E501
    tx = accounts[0].transfer(data=bytecode)
    assert tx.contract_name == "UnknownContract"
    assert web3.eth.get_code(tx.contract_address)


def test_gas_limit_and_buffer(accounts):
    with pytest.raises(ValueError):
        accounts[0].transfer(accounts[1], 1000, gas_limit=21000, gas_buffer=1.3)
