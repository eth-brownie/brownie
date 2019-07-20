#!/usr/bin/python3

test_source = '''import brownie
from brownie import project

def test_accounts(accounts, a):
    assert a == accounts
    assert accounts == brownie.accounts

def test_history(history):
    assert history == brownie.history

def test_rpc(rpc):
    assert rpc == brownie.rpc

def test_web3(web3):
    assert web3 == brownie.web3

def test_contract_container(Token, CoverageTester):
    assert Token == project.Token
    assert CoverageTester == project.CoverageTester'''


def test_fixtures(testdir):
    result = testdir.runpytest()
    result.assert_outcomes(passed=5)
