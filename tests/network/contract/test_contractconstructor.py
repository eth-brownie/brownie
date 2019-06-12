#!/usr/bin/python3

import pytest

from brownie import network, project, config
from brownie.network.contract import Contract
from brownie.network.transaction import TransactionReceipt
from brownie.exceptions import UndeployedLibrary, VirtualMachineError

accounts = network.accounts
web3 = network.web3

deploy_args = ("TST", "Test Token", 18, 1000000)


def test_returns_contract_on_success():
    '''returns a Contract instance on successful deployment'''
    c = project.Token.deploy(*deploy_args, {'from': accounts[0]})
    assert type(c) == Contract


def test_raises_on_revert():
    '''raises on revert if not in console'''
    with pytest.raises(VirtualMachineError):
        project.Token.deploy(*deploy_args, {'from': accounts[0], 'amount': 10})


def test_returns_tx_on_revert_in_console(console_mode):
    '''returns a TransactionReceipt instance on revert in the console'''
    tx = project.Token.deploy(*deploy_args, {'from': accounts[0], 'amount': 10})
    assert type(tx) == TransactionReceipt
    assert tx.status == 0


def test_nonce():
    '''nonces increment properly'''
    assert accounts[1].nonce == 0
    project.Token.deploy(*deploy_args, {'from': accounts[1]})
    assert accounts[1].nonce == 1
    network.rpc.reset()
    assert accounts[1].nonce == 0


def test_gas_price_manual():
    '''gas price is set correctly when specified in the call'''
    balance = accounts[0].balance()
    tx = project.Token.deploy(*deploy_args, {'from': accounts[0], 'gas_price': 100}).tx
    assert tx.gas_price == 100
    assert accounts[0].balance() == balance - (tx.gas_used*100)


def test_gas_price_automatic():
    '''gas price is set correctly using web3.eth.gasPrice'''
    config['active_network']['gas_price'] = False
    balance = accounts[0].balance()
    tx = project.Token.deploy(*deploy_args, {'from': accounts[0]}).tx
    assert tx.gas_price == web3.eth.gasPrice
    assert accounts[0].balance() == balance - (tx.gas_price*tx.gas_used)


def test_gas_price_config():
    '''gas price is set correctly from the config'''
    config['active_network']['gas_price'] = 50
    balance = accounts[0].balance()
    tx = project.Token.deploy(*deploy_args, {'from': accounts[0]}).tx
    assert tx.gas_price == 50
    assert accounts[0].balance() == balance - (50*tx.gas_used)


def test_gas_limit_manual():
    '''gas limit is set correctly when specified in the call'''
    tx = project.Token.deploy(*deploy_args, {'from': accounts[0], 'gas_limit': 3000000}).tx
    assert tx.gas_limit == 3000000


def test_gas_limit_automatic():
    '''gas limit is set correctly using web3.eth.estimateGas'''
    config['active_network']['gas_limit'] = False
    tx = project.Token.deploy(*deploy_args, {'from': accounts[0]}).tx
    assert tx.gas_limit == tx.gas_used


def test_gas_limit_config():
    '''gas limit is set correctly from the config'''
    config['active_network']['gas_limit'] = 5000000
    tx = project.Token.deploy(*deploy_args, {'from': accounts[0]}).tx
    assert tx.gas_limit == 5000000
    config['active_network']['gas_limit'] = False


def test_unlinked_library(clean_network):
    with pytest.raises(UndeployedLibrary):
        project.BrownieTester.deploy({'from': accounts[0]})
    lib = project.UnlinkedLib.deploy({'from': accounts[0]})
    meta = project.BrownieTester.deploy({'from': accounts[0]})
    assert lib.address[2:].lower() in meta.bytecode
