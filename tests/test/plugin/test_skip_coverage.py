#!/usr/bin/python3

test_source = '''
def test_call_and_transact(Token, accounts, skip_coverage):
    token = accounts[0].deploy(Token, "Test Token", "TST", 18, "1000 ether")
    token.transfer(accounts[1], "10 ether", {'from': accounts[0]})

def test_normal():
    assert True
'''


def test_no_skip(testdir):
    result = testdir.runpytest()
    result.assert_outcomes(passed=2)
    result = testdir.runpytest('-C')
    result.assert_outcomes(skipped=1, passed=1)
