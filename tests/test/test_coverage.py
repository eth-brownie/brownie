#!/usr/bin/python3

from brownie import rpc


def test_always_transact(testdir, methodwatch):
    rpc.reset()
    methodwatch.watch('brownie.rpc._internal_snap', 'brownie.rpc._internal_revert')
    result = testdir.runpytest("tests/call_transact.py")
    result.assert_outcomes(passed=1)
    methodwatch.assert_not_called()
    rpc.reset()
    result = testdir.runpytest("tests/call_transact.py", "--coverage")
    result.assert_outcomes(passed=1)
    methodwatch.assert_called()
