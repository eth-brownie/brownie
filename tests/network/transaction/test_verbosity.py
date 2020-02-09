#!/usr/bin/python3

import pytest


@pytest.fixture
def tx(accounts, testproject, tester):
    other = accounts[0].deploy(testproject.ExternalCallTester)
    tx = tester.makeExternalCall(other, 42)
    return tx


@pytest.fixture
def reverted_tx(accounts, tester, console_mode):
    tx = tester.revertStrings(1, {"from": accounts[0]})
    return tx


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
    i = tx.trace.index(next(i for i in tx.trace if not i["source"]))
    tx.source(i)
    assert not capfd.readouterr()[0].strip()
    tx.source(-1)
    assert capfd.readouterr()[0].strip()


def test_error(tx, reverted_tx, capfd):
    tx.error()
    assert not capfd.readouterr()[0].strip()
    reverted_tx.error()
    out = capfd.readouterr()[0].strip().split(",", maxsplit=1)[1]
    assert out
    reverted_tx.source(-1)
    assert out == capfd.readouterr()[0].strip().split(",", maxsplit=1)[1]


def test_deploy_reverts(BrownieTester, accounts, console_mode):
    tx = BrownieTester.deploy(True, {"from": accounts[0]}).tx
    with pytest.raises(NotImplementedError):
        tx.traceback()
    with pytest.raises(NotImplementedError):
        tx.call_trace()

    revertingtx = BrownieTester.deploy(False, {"from": accounts[0]})
    with pytest.raises(NotImplementedError):
        revertingtx.call_trace()
    with pytest.raises(NotImplementedError):
        revertingtx.traceback()
