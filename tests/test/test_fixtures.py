#!/usr/bin/python3

from brownie import web3


def test_test_isolation(testdir):
    result = testdir.runpytest("tests/isolation.py")
    result.assert_outcomes(passed=2)
    assert web3.eth.blockNumber == 0


def test_module_isolation(testdir):
    result = testdir.runpytest("tests/module_isolation.py")
    result.assert_outcomes(passed=2)
    assert web3.eth.blockNumber == 0


def test_session_fixtures(testdir):
    result = testdir.runpytest("tests/session_fixtures.py")
    result.assert_outcomes(passed=5)
