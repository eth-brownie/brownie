#!/usr/bin/python3

import pytest

from brownie.exceptions import VirtualMachineError
from brownie.network.transaction import TransactionReceipt

abi = {
    "constant": False,
    "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
    "name": "transfer",
    "outputs": [{"name": "", "type": "bool"}],
    "payable": False,
    "stateMutability": "nonpayable",
    "type": "function",
}


def test_attributes(tester, accounts):
    assert tester.revertStrings._address == tester.address
    assert tester.revertStrings._name == "BrownieTester.revertStrings"
    assert tester.revertStrings._owner == accounts[0]
    assert type(tester.revertStrings.abi) is dict
    assert tester.revertStrings.signature == "0xd8046e7d"


def test_encode_input(tester):
    inputs = ("hello", "0x66aB6D9362d4F35596279692F0251Db635165871", ("potato", "0x1234"))
    calldata = tester.setTuple.encode_input(inputs)
    assert calldata == (
        "0xad31c804000000000000000000000000000000000000000000000000000000000000002"
        "0000000000000000000000000000000000000000000000000000000000000006000000000"
        "000000000000000066ab6d9362d4f35596279692f0251db63516587100000000000000000"
        "000000000000000000000000000000000000000000000a000000000000000000000000000"
        "0000000000000000000000000000000000000568656c6c6f0000000000000000000000000"
        "0000000000000000000000000000000000000000000000000000000000000000000000000"
        "0000000000000000004000000000000000000000000000000000000000000000000000000"
        "0000000123400000000000000000000000000000000000000000000000000000000000000"
        "06706f7461746f0000000000000000000000000000000000000000000000000000"
    )


def test_cli_no_owner(BrownieTester, accounts, test_mode, config):
    try:
        config["pytest"]["default_contract_owner"] = False
        tester = BrownieTester.deploy(True, {"from": accounts[0]})
        assert tester.revertStrings._owner is None
    finally:
        config["pytest"]["default_contract_owner"] = True


def test_no_from(tester, accounts):
    nonce = accounts[0].nonce
    tx = tester.revertStrings(5)
    assert tx.sender == accounts[0]
    assert accounts[0].nonce == nonce + 1
    tester.revertStrings._owner = None
    with pytest.raises(AttributeError):
        tester.revertStrings(5)
    tester.revertStrings._owner = accounts[0]


def test_call(tester, accounts):
    nonce = accounts[0].nonce
    result = tester.revertStrings.call(5, {"from": accounts[0]})
    assert result is True
    assert accounts[0].nonce == nonce


def test_call_revert(tester, accounts):
    nonce = accounts[0].nonce
    with pytest.raises(VirtualMachineError):
        tester.revertStrings.call(31337, {"from": accounts[5]})
    assert accounts[0].nonce == nonce


def test_returns_tx_on_success(tester, accounts):
    """returns a TransactionReceipt on success"""
    tx = tester.revertStrings(5)
    assert type(tx) == TransactionReceipt


def test_raises_on_revert(tester, accounts):
    """raises on revert"""
    with pytest.raises(VirtualMachineError):
        tester.revertStrings(0)


def test_returns_tx_on_revert_in_console(tester, accounts, console_mode):
    """returns a tx on revert in console"""
    tx = tester.revertStrings(0)
    assert type(tx) == TransactionReceipt
    assert tx.status == 0


def test_nonce(tester, accounts):
    """nonces increment properly"""
    nonce = accounts[0].nonce
    tester.revertStrings(5, {"from": accounts[0]})
    assert accounts[0].nonce == nonce + 1


def test_balance_int(tester, accounts, web3):
    """transfers use the correct balance"""
    tester.receiveEth({"from": accounts[0], "amount": 1000000})
    assert tester.balance() == 1000000
    assert web3.eth.getBalance(tester.address) == 1000000


def test_balance_wei(tester, accounts):
    """transfer balances are converted using wei"""
    tester.receiveEth({"from": accounts[0], "amount": "1 ether"})
    assert tester.balance() == 1000000000000000000


def test_gas_price_manual(tester, accounts):
    """gas price is set correctly when specified in the call"""
    balance = accounts[0].balance()
    tx = tester.doNothing({"from": accounts[0], "gas_price": 100})
    assert tx.gas_price == 100
    assert accounts[0].balance() == balance - (100 * tx.gas_used)


def test_gas_price_automatic(tester, accounts, config, web3):
    """gas price is set correctly using web3.eth.gasPrice"""
    config["active_network"]["gas_price"] = False
    balance = accounts[0].balance()
    tx = tester.doNothing({"from": accounts[0]})
    assert tx.gas_price == web3.eth.gasPrice
    assert accounts[0].balance() == balance - (tx.gas_price * tx.gas_used)


def test_gas_price_config(tester, accounts, config):
    """gas price is set correctly from the config"""
    config["active_network"]["gas_price"] = 50
    balance = accounts[0].balance()
    tx = tester.doNothing({"from": accounts[0]})
    assert tx.gas_price == 50
    assert accounts[0].balance() == balance - (50 * tx.gas_used)


def test_gas_limit_manual(tester, accounts):
    """gas limit is set correctly when specified in the call"""
    tx = tester.doNothing({"from": accounts[0], "gas_limit": 100000})
    assert tx.gas_limit == 100000


def test_gas_limit_automatic(tester, accounts, config):
    """gas limit is set correctly using web3.eth.estimateGas"""
    config["active_network"]["gas_limit"] = False
    tx = tester.doNothing({"from": accounts[0]})
    assert tx.gas_limit == tx.gas_used


def test_gas_limit_config(tester, accounts, config):
    """gas limit is set correctly from the config"""
    config["active_network"]["gas_limit"] = 50000
    tx = tester.doNothing({"from": accounts[0]})
    assert tx.gas_limit == 50000
    config["active_network"]["gas_limit"] = False


def test_repr(tester):
    repr(tester.revertStrings)


def test_tuples(tester, accounts):
    value = ["blahblah", accounts[1], ["yesyesyes", "0x1234"]]
    tx = tester.setTuple(value)
    assert tx.status == 1
    tx = tester.getTuple.transact(accounts[1], {"from": accounts[0]})
    assert tx.status == 1
    assert tx.return_value == value
