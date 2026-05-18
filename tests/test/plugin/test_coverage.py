#!/usr/bin/python3

import json

test_source = """
import pytest

@pytest.mark.no_call_coverage
def test_call_and_transact(BrownieTester, accounts, web3, fn_isolation):
    c = accounts[0].deploy(BrownieTester, True)
    c.setNum(12, {'from': accounts[0]})
    assert web3.eth.block_number == 2
    c.getTuple(accounts[0])
    assert web3.eth.block_number == 2


def test_call_and_transact_without_decorator(BrownieTester, accounts, web3, fn_isolation):
    c = accounts[0].deploy(BrownieTester, True)
    c.setNum(12, {'from': accounts[0]})
    assert web3.eth.block_number == 2
    c.getTuple(accounts[0])
    assert web3.eth.block_number == 2
    """


def test_always_transact(plugintester, mocker, chain):
    from brownie.network import contract

    mocker.spy(contract, "_revert_transact_call")

    # without coverage eval, there should be no transact-call rollbacks
    result = plugintester.runpytest()
    result.assert_outcomes(passed=2)
    assert contract._revert_transact_call.call_count == 0

    # with coverage eval, only one of the tests should transact-and-rollback a call
    result = plugintester.runpytest("--coverage")
    result.assert_outcomes(passed=2)
    assert contract._revert_transact_call.call_count == 1


def test_coverage_tx(json_path, plugintester):
    plugintester.runpytest("-n 2")
    with json_path.open() as fp:
        build = json.load(fp)
    assert not len(build["tx"])
    plugintester.runpytest("--numprocesses=2", "--coverage")
    with json_path.open() as fp:
        build = json.load(fp)
    assert len(build["tx"]) == 3
