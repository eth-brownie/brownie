#!/usr/bin/python3

import json

from brownie import rpc

test_source = '''
def test_call_and_transact(Token, accounts, web3):
    token = accounts[0].deploy(Token, "Test Token", "TST", 18, "1000 ether")
    token.transfer(accounts[1], "10 ether", {'from': accounts[0]})
    assert web3.eth.blockNumber == 2
    assert token.balanceOf(accounts[1]) == "10 ether"
    assert web3.eth.blockNumber == 2'''

conf_source = '''
import pytest

@pytest.fixture(autouse=True)
def setup(no_call_coverage):
    pass'''


def test_always_transact(testdir, methodwatch):
    # these methods are called to revert a call-as-a-tx
    methodwatch.watch(
        'brownie.rpc._internal_snap',
        'brownie.rpc._internal_revert'
    )

    # without coverage eval
    rpc.reset()
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
    methodwatch.assert_not_called()

    # with coverage eval
    rpc.reset()
    result = testdir.runpytest('--coverage')
    result.assert_outcomes(passed=1)
    methodwatch.assert_called()
    methodwatch.reset()

    # with coverage and no_call_coverage fixture
    rpc.reset()
    testdir.makeconftest(conf_source)
    result = testdir.runpytest('--coverage')
    result.assert_outcomes(passed=1)
    methodwatch.assert_not_called()


def test_coverage_tx(json_path, testdir):
    rpc.reset()
    testdir.runpytest()
    with json_path.open() as fp:
        build = json.load(fp)
    assert not len(build['tx'])
    rpc.reset()
    testdir.runpytest('-C')
    with json_path.open() as fp:
        build = json.load(fp)
    assert len(build['tx']) == 3
