#!/usr/bin/python3


def test_load_contract_type(plugintester):
    plugintester.makeconftest(
        """
import pytest
from brownie import BrownieTester

@pytest.fixture(params=[BrownieTester, BrownieTester])
def brownie_tester(request):
    yield request.param"""
    )

    plugintester.makepyfile(
        """
def test_call_and_transact(brownie_tester, accounts, web3, fn_isolation):
    c = accounts[0].deploy(brownie_tester, True)
    c.setNum(12, {'from': accounts[0]})
    assert web3.eth.block_number == 2
    c.getTuple(accounts[0])
    assert web3.eth.block_number == 2"""
    )

    result = plugintester.runpytest("-n 2")
    result.assert_outcomes(passed=2)
