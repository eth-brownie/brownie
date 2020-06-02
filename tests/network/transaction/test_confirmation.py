#!/usr/bin/python3


def test_await_conf_simple_xfer(accounts):
    tx = accounts[0].transfer(accounts[1], "1 ether")
    assert tx.status == 1
    tx._await_confirmation(False)


def test_await_conf_successful_contract_call(accounts, tester):
    tx = tester.revertStrings(6, {"from": accounts[1]})
    assert tx.status == 1
    tx._await_confirmation(False)


def test_await_conf_failed_contract_call(accounts, tester, console_mode):
    tx = tester.revertStrings(1, {"from": accounts[1]})
    assert tx.status == 0
    tx._await_confirmation(False)


def test_await_conf_successful_contract_deploy(accounts, BrownieTester):
    tx = BrownieTester.deploy(True, {"from": accounts[0]}).tx
    assert tx.status == 1
    tx._await_confirmation(False)


def test_await_conf_failed_contract_deploy(accounts, BrownieTester, console_mode):
    tx = BrownieTester.deploy(False, {"from": accounts[0]})
    assert tx.status == 0
    tx._await_confirmation(False)


def test_transaction_confirmations(accounts, rpc):
    tx = accounts[0].transfer(accounts[1], "1 ether")
    assert tx.confirmations == 1
    rpc.mine()
    assert tx.confirmations == 2
