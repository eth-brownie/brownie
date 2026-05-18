#!/usr/bin/python3

import pytest
from hypothesis.errors import InvalidArgument

from brownie.test import given, strategy

test_source = """
from brownie.test import given, strategy
from hypothesis.errors import InvalidArgument
import pytest

@pytest.fixture(scope="module")
def tester(BrownieTester, accounts):
    tester = accounts[0].deploy(BrownieTester, True)
    yield tester

@given(value=strategy('uint256', min_value=5, exclude=31337))
def test_given(tester, web3, value):
    height = web3.eth.block_number
    tester.revertStrings(value)
    assert web3.eth.block_number == height + 1

def test_given_rejects_unknown_keyword_in_plugin():
    with pytest.raises(InvalidArgument, match="unexpected keyword argument 'value'"):

        @given(value=strategy('bool'))
        def test_missing_value_argument(web3):
            pass
    """


def test_given(plugintester):
    result = plugintester.runpytest()
    result.assert_outcomes(passed=2)


def test_given_xdist(isolatedtester):
    result = isolatedtester.runpytest("-n 2")
    result.assert_outcomes(passed=2)


def test_given_rejects_unknown_keyword():
    with pytest.raises(InvalidArgument, match="unexpected keyword argument 'value'"):

        @given(value=strategy("bool"))
        def test_missing_value_argument(web3):
            pass
