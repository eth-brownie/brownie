#!/usr/bin/python3

'''debug_traceTransaction is a very expensive call and should be avoided where
possible. These tests check that it is only being called when absolutely necessary.'''

import pytest

from brownie.network.transaction import TransactionReceipt
from brownie.project import build
from brownie import Contract


@pytest.fixture
def norevertmap():
    revert_map = build._revert_map
    build._revert_map = {}
    yield
    build._revert_map = revert_map


@pytest.fixture(autouse=True)
def mocker_spy(mocker):
    mocker.spy(TransactionReceipt, '_get_trace')
    mocker.spy(TransactionReceipt, '_expand_trace')


def test_revert_msg_get_trace_no_revert_map(console_mode, tester, norevertmap):
    '''without the revert map, getting the revert string queries the trace'''
    tx = tester.revertStrings(1)
    tx.revert_msg
    assert tx._expand_trace.call_count == 1


def test_revert_msg(console_mode, tester):
    '''dev revert string comments should not query the trace'''
    tx = tester.revertStrings(0)
    tx.revert_msg
    assert tx._get_trace.call_count == 0
    assert tx._expand_trace.call_count == 0
    tx = tester.revertStrings(1)
    tx.revert_msg
    assert tx._get_trace.call_count == 0
    assert tx._expand_trace.call_count == 0
    tx = tester.revertStrings(2)
    tx.revert_msg
    assert tx._get_trace.call_count == 0
    assert tx._expand_trace.call_count == 0
    tx = tester.revertStrings(3)
    tx.revert_msg
    assert tx._get_trace.call_count == 0
    assert tx._expand_trace.call_count == 0


def test_error_get_trace(console_mode, tester, capfd):
    '''getting the error should not query the trace'''
    tx = tester.doNothing()
    assert not tx._error_string()
    assert tx._get_trace.call_count == 0
    assert tx._expand_trace.call_count == 0
    tx = tester.revertStrings(1)
    assert tx._error_string()
    assert tx._get_trace.call_count == 0
    assert tx._expand_trace.call_count == 0


def test_revert_events(console_mode, tester):
    '''getting reverted events queries the trace but does not evaluate it'''
    tx = tester.revertStrings(1)
    assert len(tx.events) == 1
    assert 'Debug' in tx.events
    assert tx._get_trace.call_count == 1
    assert tx._expand_trace.call_count == 0


def test_modified_state(console_mode, tester):
    '''modified_state queries the trace but does not evaluate'''
    tx = tester.doNothing()
    tx.modified_state
    assert tx._get_trace.call_count == 1
    assert tx._expand_trace.call_count == 0


def test_modified_state_revert(console_mode, tester):
    tx = tester.revertStrings(1)
    assert not tx._trace
    assert tx.modified_state is False


def test_trace(tester):
    '''getting the trace also evaluates the trace'''
    tx = tester.doNothing()
    tx.trace
    assert tx._expand_trace.call_count == 1


def test_coverage_trace(accounts, tester, coverage_mode):
    '''coverage mode always evaluates the trace'''
    tx = tester.doNothing({'from': accounts[0]})
    assert tx.status == 1
    assert tx._expand_trace.call_count > 0


def test_source(tester):
    '''querying source always evaluates the trace'''
    tx = tester.doNothing()
    assert tx._get_trace.call_count == 0
    assert tx._expand_trace.call_count == 0
    tx.source(-5)
    assert tx._expand_trace.call_count == 1


def test_info(console_mode, tester):
    '''calling for info only evaluates the trace on a reverted tx'''
    tx = tester.doNothing()
    tx.info()
    assert tx._get_trace.call_count == 0
    assert tx._expand_trace.call_count == 0
    tx = tester.revertStrings(1)
    tx.info()
    assert tx._get_trace.call_count == 1
    assert tx._expand_trace.call_count == 0


def test_call_trace(console_mode, tester):
    '''call_trace always evaluates the trace'''
    tx = tester.doNothing()
    tx.call_trace()
    assert tx._get_trace.call_count == 1
    assert tx._expand_trace.call_count == 1
    tx = tester.revertStrings(1)
    tx.call_trace()
    assert tx._get_trace.call_count == 2
    assert tx._expand_trace.call_count == 2


def test_trace_deploy(tester):
    '''trace is not calculated for deploying contracts'''
    assert not tester.tx.trace


def test_trace_transfer(accounts):
    '''trace is not calculated for regular transfers of eth'''
    tx = accounts[0].transfer(accounts[1], "1 ether")
    assert not tx.trace


def test_expand_first(tester):
    '''can call _expand_trace without _get_trace first'''
    tx = tester.doNothing()
    assert tx._get_trace.call_count == 0
    assert tx._expand_trace.call_count == 0
    tx._expand_trace()
    assert tx._get_trace.call_count == 1


def test_expand_multiple(tester):
    '''multiple calls to get_trace and expand_trace should not raise'''
    tx = tester.doNothing()
    tx._expand_trace()
    tx._get_trace()
    tx._expand_trace()
    tx = tester.doNothing()
    tx._get_trace()
    tx._expand_trace()
    tx._get_trace()


def test_revert_string_from_trace(console_mode, tester):
    tx = tester.revertStrings(0)
    msg = tx.revert_msg
    tx.revert_msg = None
    tx._reverted_trace(tx.trace)
    assert tx.revert_msg == msg


def test_inlined_library_jump(accounts, tester):
    tx = tester.useSafeMath(6, 7)
    assert max([i['jumpDepth'] for i in tx.trace]) == 1


def test_external_jump(accounts, testproject, tester):
    ext = accounts[0].deploy(testproject.ExternalCallTester)
    tx = tester.makeExternalCall(ext, 4)
    assert max([i['depth'] for i in tx.trace]) == 1
    assert max([i['jumpDepth'] for i in tx.trace]) == 0


def test_delegatecall_jump(accounts, librarytester):
    accounts[0].deploy(librarytester['TestLib'])
    contract = accounts[0].deploy(librarytester['Unlinked'])
    tx = contract.callLibrary(6, 7)
    assert max([i['depth'] for i in tx.trace]) == 1
    assert max([i['jumpDepth'] for i in tx.trace]) == 0


def test_unknown_contract(accounts, testproject, tester):
    ext = accounts[0].deploy(testproject.ExternalCallTester)
    tx = tester.makeExternalCall(ext, 4)
    del testproject.ExternalCallTester[0]
    tx.call_trace()


def test_contractabi(accounts, testproject, tester):
    ext = accounts[0].deploy(testproject.ExternalCallTester)
    tx = tester.makeExternalCall(ext, 4)
    del testproject.ExternalCallTester[0]
    ext = Contract(ext.address, "ExternalTesterABI", ext.abi)
    tx.call_trace()
