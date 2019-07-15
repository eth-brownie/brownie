#!/usr/bin/python3

from brownie.test import output


def test_config_gas(testdir, callcatch):
    callcatch.patch(output, 'print_gas_profile')
    assert not callcatch
    testdir.runpytest("tests/reverts.py", '--gas')
    assert callcatch
    callcatch.reset()
    assert not callcatch
    testdir.runpytest("tests/reverts.py")
    assert not callcatch
    testdir.runpytest("tests/reverts.py", '-G')
    assert callcatch


def test_config_coverage(testdir, callcatch):
    callcatch.patch(output, 'print_coverage_totals')
    assert not callcatch
    testdir.runpytest("tests/reverts.py", '--coverage')
    assert callcatch
    callcatch.reset()
    assert not callcatch
    testdir.runpytest("tests/reverts.py")
    assert not callcatch
    testdir.runpytest("tests/reverts.py", '-C')
    assert callcatch
