#!/usr/bin/python3

test_source = [
    """
import brownie
import pytest

@pytest.fixture(scope="module")
def tester(BrownieTester, accounts):
    tester = accounts[0].deploy(BrownieTester, True)
    yield tester

def test_reverts_success(tester):
    with brownie.reverts("zero"):
        tester.revertStrings(0)
    with brownie.reverts(dev_revert_msg="dev: one"):
        tester.revertStrings(1)

@pytest.mark.xfail(condition=True, reason="", raises=AssertionError, strict=True)
def test_reverts_incorrect_msg(tester):
    with brownie.reverts("potato"):
        tester.revertStrings(0)
    """,
    """
import brownie
import pytest

@pytest.mark.xfail(condition=True, reason="", raises=TypeError, strict=True)
def test_reverts_wrong_excetion():
    with brownie.reverts("potato"):
        12 + "horse"

@pytest.mark.xfail(condition=True, reason="", raises=AssertionError, strict=True)
def test_does_not_revert():
    with brownie.reverts():
        1 + 2
    """,
]


def test_revert_manager(plugintester):
    result = plugintester.runpytest()
    result.assert_outcomes(passed=1, xfailed=3)


def test_revert_manager_xdist(isolatedtester):
    result = isolatedtester.runpytest("-n 2")
    result.assert_outcomes(passed=1, xfailed=3)
