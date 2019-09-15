#!/usr/bin/python3

test_source = """
def test_call_and_transact(BrownieTester, accounts, skip_coverage):
    c = accounts[0].deploy(BrownieTester, True)
    c.doNothing({'from': accounts[0]})

def test_normal():
    assert True
"""


def test_no_skip(plugintester):
    result = plugintester.runpytest()
    result.assert_outcomes(passed=2)


def test_no_skip_coverage(plugintester):
    result = plugintester.runpytest("-C")
    result.assert_outcomes(skipped=1, passed=1)
