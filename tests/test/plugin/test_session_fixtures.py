#!/usr/bin/python3

test_source = [
    """
import brownie

def test_accounts(accounts, a):
    assert a == accounts
    assert accounts == brownie.accounts
    assert len(a)

def test_history(history):
    assert history == brownie.history

def test_rpc(rpc):
    assert rpc == brownie.rpc

def test_web3(web3):
    assert web3 == brownie.web3
    """,
    """
from brownie.network.contract import ContractContainer

def test_contract_container(BrownieTester, EVMTester):
    assert type(BrownieTester) is ContractContainer
    assert type(EVMTester) is ContractContainer
    """,
]


def test_fixtures(plugintester):
    result = plugintester.runpytest()
    result.assert_outcomes(passed=5)


def test_fixtures_xdist(isolatedtester):
    result = isolatedtester.runpytest("-n 2")
    result.assert_outcomes(passed=5)
