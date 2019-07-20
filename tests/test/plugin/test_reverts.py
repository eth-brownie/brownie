#!/usr/bin/python3

test_source = '''import pytest

@pytest.fixture(scope="module")
def tester(UnlinkedLib, BrownieTester, accounts):
    accounts[0].deploy(UnlinkedLib)
    tester = accounts[0].deploy(BrownieTester)
    yield tester

def test_reverts_success(tester):
    with pytest.reverts("zero"):
        tester.testRevertStrings(0)
    with pytest.reverts("dev: one"):
        tester.testRevertStrings(1)

@pytest.mark.xfail(condition=True, reason="", raises=AssertionError, strict=True)
def test_reverts_incorrect_msg(tester):
    with pytest.reverts("potato"):
        tester.testRevertStrings(0)

@pytest.mark.xfail(condition=True, reason="", raises=TypeError, strict=True)
def test_reverts_wrong_excetion(tester):
    with pytest.reverts("potato"):
        12 + "horse"

@pytest.mark.xfail(condition=True, reason="", raises=AssertionError, strict=True)
def test_does_not_revert(tester):
    with pytest.reverts():
        1 + 2'''


def test_revert_manager(testdir):
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, xfailed=3)
