#!/usr/bin/python3

import pytest

from brownie import accounts, config
from brownie._config import ARGV


@pytest.fixture(scope="module")
def tx(token):
    tx = token.transfer(accounts[1], 100)
    yield tx
    config['logging']['tx'] = 1


@pytest.fixture(scope="module")
def reverted_tx(token):
    ARGV['cli'] = "console"
    tx = token.transferFrom(accounts[4], accounts[1], 100)
    ARGV['cli'] = False
    yield tx
    config['logging']['tx'] = 1


def test_info(tx):
    config['logging']['tx'] = 2
    info = tx.info()
    config['logging']['tx'] = 1
    assert info == tx.info()


def test_confirm_output(tx):
    config['logging']['tx'] = 2
    info = tx._confirm_output()
    config['logging']['tx'] = 1
    assert info != tx._confirm_output()


def test_traceback(tx, reverted_tx):
    assert reverted_tx.traceback()
    assert not tx.traceback()


def test_call_trace(tx, reverted_tx):
    assert tx.call_trace()
    assert reverted_tx.call_trace()


def test_source(tx):
    i = tx.trace.index(next(i for i in tx.trace if not i['source']))
    assert not tx.source(i)
    assert tx.source(-1)


def test_error(tx, reverted_tx):
    assert not tx.error()
    assert reverted_tx.error()
    assert reverted_tx.error() == reverted_tx.source(-1)
