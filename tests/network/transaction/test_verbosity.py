#!/usr/bin/python3

from copy import deepcopy
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


def test_info(tx, capfd):
    config['logging']['tx'] = 2
    tx.info()
    out = capfd.readouterr()[0].strip()
    config['logging']['tx'] = 1
    tx.info()
    assert out == capfd.readouterr()[0].strip()


def test_confirm_output(tx):
    config['logging']['tx'] = 2
    info = tx._confirm_output()
    config['logging']['tx'] = 1
    assert info != tx._confirm_output()


def test_traceback(tx, reverted_tx, capfd):
    reverted_tx.traceback()
    assert capfd.readouterr()[0].strip()
    tx.traceback()
    assert not capfd.readouterr()[0].strip()


def test_call_trace(tx, reverted_tx, capfd):
    tx.call_trace()
    assert capfd.readouterr()[0].strip()
    reverted_tx.call_trace()
    assert capfd.readouterr()[0].strip()


def test_source(tx, capfd):
    i = tx.trace.index(next(i for i in tx.trace if not i['source']))
    tx.source(i)
    assert not capfd.readouterr()[0].strip()
    tx.source(-1)
    assert capfd.readouterr()[0].strip()


def test_error(tx, reverted_tx, capfd):
    tx.error()
    assert not capfd.readouterr()[0].strip()
    reverted_tx.error()
    out = capfd.readouterr()[0].strip()
    assert out
    reverted_tx.source(-1)
    assert out == capfd.readouterr()[0].strip()


def test_deploy_reverts(token):
    tx = deepcopy(token.tx)
    tx.status = 0
    with pytest.raises(NotImplementedError):
        tx.call_trace()
    with pytest.raises(NotImplementedError):
        tx.traceback()
