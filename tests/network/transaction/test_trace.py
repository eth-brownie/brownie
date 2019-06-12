#!/usr/bin/python3

'''debug_traceTransaction is a very expensive call and should be avoided where
possible. These tests check that it is only being called when absolutely necessary.'''

from brownie import accounts, project
from brownie.project import build


def test_revert_msg(console_mode, tester):
    '''dev revert string comments should be correct and not query the trace'''
    tx = tester.testRevertStrings(0)
    tx.revert_msg
    assert not tx._trace
    tx = tester.testRevertStrings(1)
    tx.revert_msg
    assert not tx._trace
    tx = tester.testRevertStrings(2)
    tx.revert_msg
    assert not tx._trace
    tx = tester.testRevertStrings(3)
    tx.revert_msg
    assert not tx._trace


def test_revert_msg_get_trace_no_revert_map(console_mode, tester):
    '''without the revert map, getting the revert string queries the trace'''
    revert_map = build._revert_map
    build._revert_map = {}
    try:
        tx = tester.testRevertStrings(1)
        tx.revert_msg
        assert 'trace' in tx.__dict__
    finally:
        build._revert_map = revert_map


def test_error_get_trace(console_mode, tester):
    '''getting the error should not query the trace'''
    tx = tester.doNothing()
    assert not tx.error()
    assert not tx._trace
    tx = tester.testRevertStrings(1)
    assert tx.error()
    assert not tx._trace


def test_revert_events(console_mode, tester):
    '''getting reverted events queries the trace but does not evaluate it'''
    tx = tester.testRevertStrings(1)
    assert len(tx.events) == 1
    assert 'Debug' in tx.events
    assert tx._trace
    assert 'trace' not in tx.__dict__


def test_modified_state(console_mode, tester):
    '''modified_state queries the trace but does not evaluate'''
    tx = tester.doNothing()
    tx.modified_state
    assert tx._trace
    assert 'trace' not in tx.__dict__


def test_modified_state_revert(console_mode, tester):
    tx = tester.testRevertStrings(1)
    assert not tx._trace
    assert tx.modified_state is False


def test_trace(tester):
    '''getting the trace also evaluates the trace'''
    tx = tester.doNothing()
    tx.trace
    assert 'trace' in tx.__dict__


def test_coverage_trace(coverage_mode, tester):
    '''coverage mode always evaluates the trace'''
    tx = tester.doNothing()
    assert tx.status == 1
    assert 'trace' in tx.__dict__


def test_source(tester):
    '''querying source always evaluates the trace'''
    tx = tester.doNothing()
    assert 'trace' not in tx.__dict__
    tx.source(-5)
    assert 'trace' in tx.__dict__


def test_info(console_mode, tester):
    '''calling for info only evaluates the trace on a reverted tx'''
    tx = tester.doNothing()
    assert not tx._trace
    tx.info()
    assert not tx._trace
    tx = tester.testRevertStrings(1)
    tx.info()
    assert tx._trace


def test_call_trace(console_mode, tester):
    '''call_trace always evaluates the trace'''
    tx = tester.doNothing()
    assert not tx._trace
    tx.call_trace()
    assert 'trace' in tx.__dict__
    tx = tester.testRevertStrings(1)
    tx.call_trace()
    assert 'trace' in tx.__dict__


def test_trace_deploy(tester):
    '''trace is not calculated for deploying contracts'''
    assert not tester.tx.trace


def test_trace_transfer():
    '''trace is not calculated for regular transfers of eth'''
    tx = accounts[0].transfer(accounts[1], "1 ether")
    assert not tx.trace


def test_expand_first(tester):
    '''can call _expand_trace without _get_trace first'''
    tx = tester.doNothing()
    assert not tx._trace
    tx._expand_trace()
    assert 'trace' in tx.__dict__


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


def test_external_jump():
    ext = accounts[0].deploy(project.ExternalCallTester)
    other = accounts[0].deploy(project.Other)
    tx = ext.doNotCall(other)
    assert not next((i for i in tx.trace if i['depth'] != 0), False)
    tx = ext.callAnother(other, 4)
    assert next(i for i in tx.trace if i['depth'] != 0)


def test_revert_string_from_trace(console_mode, tester):
    tx = tester.testRevertStrings(0)
    msg = tx.revert_msg
    tx.revert_msg = None
    tx._reverted_trace(tx.trace)
    assert tx.revert_msg == msg
