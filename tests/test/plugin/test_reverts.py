#!/usr/bin/python3

test_source = [
    """
import pytest

@pytest.fixture(scope="module")
def tester(BrownieTester, accounts):
    tester = accounts[0].deploy(BrownieTester, True)
    yield tester

def test_reverts_success(tester):
    with pytest.reverts("zero"):
        tester.revertStrings(0)
    with pytest.reverts("dev: one"):
        tester.revertStrings(1)

@pytest.mark.xfail(condition=True, reason="", raises=AssertionError, strict=True)
def test_reverts_incorrect_msg(tester):
    with pytest.reverts("potato"):
        tester.revertStrings(0)
    """,
    """
import pytest

@pytest.mark.xfail(condition=True, reason="", raises=TypeError, strict=True)
def test_reverts_wrong_excetion():
    with pytest.reverts("potato"):
        12 + "horse"

@pytest.mark.xfail(condition=True, reason="", raises=AssertionError, strict=True)
def test_does_not_revert():
    with pytest.reverts():
        1 + 2
    """,
]


def test_revert_manager(plugintester):
    result = plugintester.runpytest()
    result.assert_outcomes(passed=1, xfailed=3)


def test_revert_manager_xdist(isolatedtester):
    result = isolatedtester.runpytest("-n 2")
    result.assert_outcomes(passed=1, xfailed=3)
