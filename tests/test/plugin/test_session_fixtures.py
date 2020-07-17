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

def test_interface(interface):
    assert isinstance(interface, brownie.network.contract.InterfaceContainer)

def test_chain(chain):
    assert chain == brownie.chain

def test_rpc(rpc):
    assert rpc == brownie.rpc

def test_web3(web3):
    assert web3 == brownie.web3
    """,
    """
from brownie.network.contract import ContractContainer
from brownie import EVMTester

def test_contract_container(BrownieTester):
    assert type(BrownieTester) is ContractContainer
    assert type(EVMTester) is ContractContainer
    """,
    """
from brownie.test import state_machine as sf

def test_state_machine(state_machine):
    assert state_machine == sf
    """,
]


def test_fixtures(plugintester):
    result = plugintester.runpytest()
    result.assert_outcomes(passed=8)


def test_fixtures_xdist(isolatedtester):
    result = isolatedtester.runpytest("-n 2")
    result.assert_outcomes(passed=8)
