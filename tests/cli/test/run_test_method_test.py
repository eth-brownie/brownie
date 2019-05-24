#!/usr/bin/python3

import pytest

from brownie.cli import test
from brownie import accounts, project, config, history, rpc
from brownie.types import FalseyDict
from brownie.exceptions import ExpectedFailing


@pytest.fixture(autouse=True, scope="module")
def setup():
    global __file__
    __file__ = config['folders']['project']+"/tests/faketest.py"


@pytest.fixture(scope="module")
def printer():
    p = test.TestPrinter(__file__, 1, 100)
    yield p
    p.finish()


def _passes():
    t = accounts[1].deploy(project.Token, "", "", 0, 100000)
    t.balanceOf(accounts[1])


def _reverts():
    t = accounts[1].deploy(project.Token, "", "", 0, 0)
    t.transfer(accounts[2], 10000, {'from': accounts[0]})


# no coverage tests

def test_check_return_no_coverage(printer):
    tb, cov = test.run_test_method(_passes, FalseyDict(), {}, printer)
    assert not tb
    assert not cov
    tb, cov = test.run_test_method(_reverts, FalseyDict(), {}, printer)
    assert tb
    assert not cov


def test_skip(printer):
    tb, _ = test.run_test_method(_reverts, FalseyDict({'skip': True}), {}, printer)
    assert not tb
    tb, _ = test.run_test_method(_reverts, FalseyDict({'skip': "coverage"}), {}, printer)
    assert tb


def test_always_transact_no_coverage(printer, clean_network):
    assert not history
    test.run_test_method(_passes, FalseyDict({'always_transact': True}), {}, printer)
    assert len(history) == 1
    rpc.reset()
    assert not history
    test.run_test_method(_passes, FalseyDict({'always_transact': False}), {}, printer)
    assert len(history) == 1


def test_pending(printer):
    tb, cov = test.run_test_method(_passes, FalseyDict({'pending': True}), {}, printer)
    assert tb
    assert tb[0][2] == ExpectedFailing
    assert not cov
    tb, cov = test.run_test_method(_reverts, FalseyDict({'pending': True}), {}, printer)
    assert not tb
    assert not cov


# coverage tests

def test_check_return_coverage(printer, coverage_mode):
    tb, cov = test.run_test_method(_passes, FalseyDict(), {}, printer)
    assert not tb
    assert cov
    tb, cov = test.run_test_method(_reverts, FalseyDict(), {}, printer)
    assert tb
    assert not cov


def test_skip_coverage(printer, coverage_mode):
    tb, _ = test.run_test_method(_reverts, FalseyDict({'skip': "coverage"}), {}, printer)
    assert not tb


def test_always_transact_coverage(printer, clean_network, coverage_mode):
    assert not history
    test.run_test_method(_passes, FalseyDict({'always_transact': True}), {}, printer)
    assert len(history) == 2
    rpc.reset()
    assert not history
    test.run_test_method(_passes, FalseyDict({'always_transact': False}), {}, printer)
    assert len(history) == 1


def test_pending_coverage(printer, coverage_mode):
    tb, cov = test.run_test_method(_passes, FalseyDict({'pending': True}), {}, printer)
    assert tb
    assert tb[0][2] == ExpectedFailing
    assert not cov
    tb, cov = test.run_test_method(_reverts, FalseyDict({'pending': True}), {}, printer)
    assert not tb
    assert not cov
