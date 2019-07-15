#!/usr/bin/python3


def test_reverts(testdir):
    result = testdir.runpytest("tests/reverts.py")
    result.assert_outcomes(passed=1, xfailed=3)
