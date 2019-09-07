#!/usr/bin/python3

test_source = '''import brownie
from brownie.network.contract import ContractContainer

def test_accounts(accounts, a):
    assert a == accounts
    assert accounts == brownie.accounts

def test_history(history):
    assert history == brownie.history

def test_rpc(rpc):
    assert rpc == brownie.rpc

def test_web3(web3):
    assert web3 == brownie.web3

def test_contract_container(BrownieTester, EVMTester):
    assert type(BrownieTester) is ContractContainer
    assert type(EVMTester) is ContractContainer'''


def test_fixtures(plugintester):
    result = plugintester.runpytest()
    result.assert_outcomes(passed=5)
