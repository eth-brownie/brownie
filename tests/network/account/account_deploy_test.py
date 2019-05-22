#!/usr/bin/python3

import pytest

from brownie import network, project, config
from brownie.exceptions import UndeployedLibrary, VirtualMachineError
from brownie._config import ARGV
from brownie.network.contract import Contract
from brownie.network.transaction import TransactionReceipt


accounts = network.accounts
web3 = network.web3


def test_returns_contract_on_success():
    '''returns a Contract instance on successful deployment'''
    c = accounts[0].deploy(project.Token, "TST", "Test Token", 18, 1000000)
    assert type(c) == Contract


def test_raises_on_revert():
    '''raises on revert if not in console'''
    with pytest.raises(VirtualMachineError):
        accounts[0].deploy(project.Token, "TST", "Test Token", 18, 1000000, amount=10)


def test_returns_tx_on_revert_in_console():
    '''returns a TransactionReceipt instance on revert in the console'''
    ARGV['cli'] = "console"
    try:
        tx = accounts[0].deploy(project.Token, "TST", "Test Token", 18, 1000000, amount=10)
        assert type(tx) == TransactionReceipt
        assert tx.status == 0
    finally:
        ARGV['cli'] = False


def test_nonce():
    '''nonces increment properly'''
    assert accounts[1].nonce == 0
    accounts[1].deploy(project.Token, "TST", "Test Token", 18, 1000000)
    assert accounts[1].nonce == 1
    network.rpc.reset()
    assert accounts[1].nonce == 0


def test_gas_price_manual():
    '''gas price is set correctly when specified in the call'''
    balance = accounts[0].balance()
    tx = accounts[0].deploy(project.Token, "TST", "Test Token", 18, 1000000, gas_price=100).tx
    assert tx.gas_price == 100
    assert accounts[0].balance() == balance - (tx.gas_used*100)


def test_gas_price_automatic():
    '''gas price is set correctly using web3.eth.gasPrice'''
    config['active_network']['gas_price'] = False
    balance = accounts[0].balance()
    tx = accounts[0].deploy(project.Token, "TST", "Test Token", 18, 1000000).tx
    assert tx.gas_price == web3.eth.gasPrice
    assert accounts[0].balance() == balance - (tx.gas_price*tx.gas_used)


def test_gas_price_config():
    '''gas price is set correctly from the config'''
    config['active_network']['gas_price'] = 50
    balance = accounts[0].balance()
    tx = accounts[0].deploy(project.Token, "TST", "Test Token", 18, 1000000).tx
    assert tx.gas_price == 50
    assert accounts[0].balance() == balance - (50*tx.gas_used)


def test_gas_limit_manual():
    '''gas limit is set correctly when specified in the call'''
    tx = accounts[0].deploy(project.Token, "TST", "Test Token", 18, 1000000, gas_limit=3000000).tx
    assert tx.gas_limit == 3000000


def test_gas_limit_automatic():
    '''gas limit is set correctly using web3.eth.estimateGas'''
    config['active_network']['gas_limit'] = False
    tx = accounts[0].deploy(project.Token, "TST", "Test Token", 18, 1000000).tx
    assert tx.gas_limit == tx.gas_used


def test_gas_limit_config():
    '''gas limit is set correctly from the config'''
    config['active_network']['gas_limit'] = 5000000
    tx = accounts[0].deploy(project.Token, "TST", "Test Token", 18, 1000000).tx
    assert tx.gas_limit == 5000000
    config['active_network']['gas_limit'] = False


def test_unlinked_library():
    network.rpc.reset()
    with pytest.raises(UndeployedLibrary):
        accounts[0].deploy(project.BrownieTester)
    lib = accounts[0].deploy(project.UnlinkedLib)
    meta = accounts[0].deploy(project.BrownieTester)
    assert lib.address[2:].lower() in meta.bytecode
    network.rpc.reset()
