#!/usr/bin/python3

test_source = """
from brownie.test import given, strategy
import pytest

@pytest.fixture(scope="module")
def tester(BrownieTester, accounts):
    tester = accounts[0].deploy(BrownieTester, True)
    yield tester

@given(value=strategy('uint256', min_value=5, exclude=31337))
def test_given(tester, web3, value):
    tester.revertStrings(value)
    assert web3.eth.block_number == 2

@given(value=strategy('bool'))
def test_given_fails(web3):
    # should fail because value is not a keyword argument
    pass
    """


def test_given(plugintester):
    result = plugintester.runpytest()
    result.assert_outcomes(passed=1, failed=1)


def test_given_xdist(isolatedtester):
    result = isolatedtester.runpytest("-n 2")
    result.assert_outcomes(passed=1, failed=1)
