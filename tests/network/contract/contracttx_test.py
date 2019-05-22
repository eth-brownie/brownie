#!/usr/bin/python3

import pytest

from brownie import network, project, config, web3
from brownie.exceptions import VirtualMachineError
from brownie.network.transaction import TransactionReceipt

accounts = network.accounts
abi = {
        'constant': False,
        'inputs': [
            {'name': '_to', 'type': 'address'},
            {'name': '_value', 'type': 'uint256'}
        ],
        'name': 'transfer',
        'outputs': [{'name': '', 'type': 'bool'}],
        'payable': False,
        'stateMutability': 'nonpayable',
        'type': 'function'
    }


def test_attributes(token):
    assert token.transfer._address == token.address
    assert token.transfer._name == "Token.transfer"
    assert token.transfer._owner == accounts[0]
    assert token.transfer.abi == abi
    assert token.transfer.signature == "0xa9059cbb"


def test_encode_abi(token):
    assert token.transfer.encode_abi(
        "0x2f084926Fd8A120089cA5F622975Fe7F1306AFF9",
        10000
    ) == (
        "0xa9059cbb0000000000000000000000002f084926fd8a120089ca5f622975fe7f1306aff9"
        "0000000000000000000000000000000000000000000000000000000000002710"
    )


def test_cli_no_owner(test_mode):
    try:
        config['test']['default_contract_owner'] = False
        token = project.Token.deploy("", "", 18, 1000000, {'from': accounts[0]})
        assert token.transfer._owner is None
    finally:
        config['test']['default_contract_owner'] = True


def test_no_from(token):
    nonce = accounts[0].nonce
    tx = token.transfer(accounts[1], 1000)
    assert tx.sender == accounts[0]
    assert accounts[0].nonce == nonce + 1


def test_call(token):
    nonce = accounts[0].nonce
    result = token.transfer.call(accounts[1], 1000, {'from': accounts[0]})
    assert result is True
    assert accounts[0].nonce == nonce


def test_call_revert(token):
    nonce = accounts[0].nonce
    with pytest.raises(VirtualMachineError):
        token.transfer.call(accounts[1], 1000, {'from': accounts[5]})
    assert accounts[0].nonce == nonce


def test_returns_tx_on_success(token):
    '''returns a TransactionReceipt on success'''
    tx = token.transfer(accounts[1], 1000)
    assert type(tx) == TransactionReceipt


def test_raises_on_revert(token):
    '''raises on revert'''
    with pytest.raises(VirtualMachineError):
        token.transfer(accounts[1], 10000000000000)


def test_returns_tx_on_revert_in_console(console_mode, token):
    '''returns a tx on revert in console'''
    tx = token.transfer(accounts[1], 10000000000000)
    assert type(tx) == TransactionReceipt
    assert tx.status == 0


def test_nonce(token):
    '''nonces increment properly'''
    nonce = accounts[0].nonce
    token.transfer(accounts[1], 1000, {'from': accounts[0]})
    assert accounts[0].nonce == nonce + 1


def test_balance_int(tester):
    '''transfers use the correct balance'''
    network.rpc.snapshot()
    tester.receiveEth({'from': accounts[1], 'amount': 1000000})
    assert tester.balance() == 1000000
    assert web3.eth.getBalance(tester.address) == 1000000
    network.rpc.revert()


def test_balance_wei(tester):
    '''transfer balances are converted using wei'''
    tester.receiveEth({'from': accounts[1], 'amount': "1 ether"})
    assert tester.balance() == 1000000000000000000


def test_gas_price_manual(tester):
    '''gas price is set correctly when specified in the call'''
    balance = accounts[0].balance()
    tx = tester.doNothing({'from': accounts[0], 'gas_price': 100})
    assert tx.gas_price == 100
    assert accounts[0].balance() == balance - (100*tx.gas_used)


def test_gas_price_automatic(tester):
    '''gas price is set correctly using web3.eth.gasPrice'''
    config['active_network']['gas_price'] = False
    balance = accounts[0].balance()
    tx = tester.doNothing({'from': accounts[0]})
    assert tx.gas_price == web3.eth.gasPrice
    assert accounts[0].balance() == balance - (tx.gas_price*tx.gas_used)


def test_gas_price_config(tester):
    '''gas price is set correctly from the config'''
    config['active_network']['gas_price'] = 50
    balance = accounts[0].balance()
    tx = tester.doNothing({'from': accounts[0]})
    assert tx.gas_price == 50
    assert accounts[0].balance() == balance - (50*tx.gas_used)


def test_gas_limit_manual(tester):
    '''gas limit is set correctly when specified in the call'''
    tx = tester.doNothing({'from': accounts[0], 'gas_limit': 100000})
    assert tx.gas_limit == 100000


def test_gas_limit_automatic(tester):
    '''gas limit is set correctly using web3.eth.estimateGas'''
    config['active_network']['gas_limit'] = False
    tx = tester.doNothing({'from': accounts[0]})
    assert tx.gas_limit == tx.gas_used


def test_gas_limit_config(tester):
    '''gas limit is set correctly from the config'''
    config['active_network']['gas_limit'] = 50000
    tx = tester.doNothing({'from': accounts[0]})
    assert tx.gas_limit == 50000
    config['active_network']['gas_limit'] = False
