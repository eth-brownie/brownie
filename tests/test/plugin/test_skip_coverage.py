#!/usr/bin/python3

import pytest

test_source = """
import brownie
import pytest

@pytest.mark.skip_coverage
def test_call_and_transact(BrownieTester, accounts):
    c = accounts[0].deploy(BrownieTester, True)
    c.doNothing({'from': accounts[0]})

def test_normal():
    assert True
"""


@pytest.mark.parametrize("arg", ["", "-n 2"])
def test_no_skip(isolatedtester, arg):
    result = isolatedtester.runpytest(arg)
    result.assert_outcomes(passed=2)


@pytest.mark.parametrize("arg", ["", "-n 1"])
def test_no_skip_coverage(isolatedtester, arg):
    result = isolatedtester.runpytest("-C", arg)
    result.assert_outcomes(skipped=1, passed=1)
