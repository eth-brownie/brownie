#!/usr/bin/python3


def test_config_gas(testdir, methodwatch):
    methodwatch.watch('brownie.test.output.print_gas_profile')
    methodwatch.assert_not_called()
    testdir.runpytest("tests/reverts.py", '--gas')
    methodwatch.assert_called()
    methodwatch.reset()
    methodwatch.assert_not_called()
    testdir.runpytest("tests/reverts.py")
    methodwatch.assert_not_called()
    testdir.runpytest("tests/reverts.py", '-G')
    methodwatch.assert_called()


def test_config_coverage(testdir, methodwatch):
    methodwatch.watch('brownie.test.output.print_coverage_totals')
    methodwatch.assert_not_called()
    testdir.runpytest("tests/reverts.py", '--coverage')
    methodwatch.assert_called()
    methodwatch.reset()
    methodwatch.assert_not_called()
    testdir.runpytest("tests/reverts.py")
    methodwatch.assert_not_called()
    testdir.runpytest("tests/reverts.py", '-C')
    methodwatch.assert_called()
