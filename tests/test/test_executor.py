#!/usr/bin/python3

from brownie import test
from brownie.test import executor


def test_run_test_modules_update():
    paths = ['tests/brownie-test-project/tests/token/transfer.py']
    assert executor.run_test_modules(paths, only_update=False) is True
    assert executor.run_test_modules(paths, only_update=True) is None
    assert executor.run_test_modules(paths, only_update=False) is True


def test_run_test_modules_skip_only_coverage():
    paths = ['tests/brownie-test-project/tests/token/approve_transferFrom.py']
    assert executor.run_test_modules(paths) is False
    assert executor.run_test_modules(paths, check_coverage=True) is True


def test_main_run_tests():
    test.run_tests('tests/brownie-test-project')
    test.run_tests('tests/brownie-test-project', check_coverage=True, gas_profile=True)
