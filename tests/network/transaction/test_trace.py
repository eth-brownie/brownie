#!/usr/bin/python3

"""debug_traceTransaction is a very expensive call and should be avoided where
possible. These tests check that it is only being called when absolutely necessary."""

import pytest

from brownie import Contract
from brownie.exceptions import RPCRequestError
from brownie.network.transaction import TransactionReceipt
from brownie.project import build


@pytest.fixture
def norevertmap():
    revert_map = build._revert_map
    build._revert_map = {}
    yield
    build._revert_map = revert_map


@pytest.fixture(autouse=True)
def mocker_spy(mocker):
    mocker.spy(TransactionReceipt, "_get_trace")
    mocker.spy(TransactionReceipt, "_expand_trace")


def test_revert_msg_get_trace_no_revert_map(console_mode, tester, norevertmap):
    """without the revert map, getting the revert string queries the trace"""
    tx = tester.revertStrings(1)
    tx.revert_msg
    assert tx._expand_trace.call_count


@pytest.mark.xfail(reason="Issue with ganache 7, should be fixed but not critical")
def test_revert_msg(console_mode, tester):
    """dev revert string comments should not query the trace"""
    tx = tester.revertStrings(0)
    tx.revert_msg
    assert not tx._get_trace.call_count
    assert not tx._expand_trace.call_count
    tx = tester.revertStrings(1)
    tx.revert_msg
    assert not tx._get_trace.call_count
    assert not tx._expand_trace.call_count
    tx = tester.revertStrings(2)
    tx.revert_msg
    assert not tx._get_trace.call_count
    assert not tx._expand_trace.call_count
    tx = tester.revertStrings(3)
    tx.revert_msg
    assert not tx._get_trace.call_count
    assert not tx._expand_trace.call_count


@pytest.mark.xfail(reason="Issue with ganache 7, should be fixed but not critical")
def test_error_get_trace(console_mode, tester, capfd):
    """getting the error should not query the trace"""
    tx = tester.doNothing()
    assert not tx._error_string()
    assert not tx._get_trace.call_count
    assert not tx._expand_trace.call_count
    tx = tester.revertStrings(1)
    assert tx._error_string()
    assert not tx._get_trace.call_count
    assert not tx._expand_trace.call_count


def test_revert_events(console_mode, tester):
    """getting reverted events queries the trace but does not evaluate it"""
    tx = tester.revertStrings(1)
    assert len(tx.events) == 1
    assert "Debug" in tx.events
    assert tx._get_trace.call_count
    assert not tx._expand_trace.call_count


def test_modified_state(console_mode, tester):
    """modified_state queries the trace but does not evaluate"""
    tx = tester.doNothing()
    tx.modified_state
    assert tx._get_trace.call_count
    assert not tx._expand_trace.call_count


def test_modified_state_revert(console_mode, tester):
    tx = tester.revertStrings(1)
    assert not tx._trace
    assert tx.modified_state is False


def test_new_contracts(console_mode, tester):
    tx = tester.doNothing()
    assert tx.new_contracts == []
    assert tx._expand_trace.call_count


def test_new_contracts_reverts(console_mode, tester):
    tx = tester.revertStrings(1)
    assert tx.new_contracts == []
    assert not tx._trace


def test_internal_xfers(tester):
    tx = tester.doNothing()
    assert tx.internal_transfers == []
    assert tx._expand_trace.call_count


def test_internal_xfers_reverts(console_mode, tester):
    tx = tester.revertStrings(1)
    assert tx.internal_transfers == []
    assert not tx._trace


def test_trace(tester):
    """getting the trace also evaluates the trace"""
    tx = tester.doNothing()
    tx.trace
    assert tx._expand_trace.call_count


def test_coverage_trace(accounts, tester, coverage_mode):
    """coverage mode always evaluates the trace"""
    tx = tester.doNothing({"from": accounts[0]})
    assert tx.status == 1
    assert tx._expand_trace.call_count


def test_source(tester):
    """querying source always evaluates the trace"""
    tx = tester.doNothing()
    assert not tx._get_trace.call_count
    assert not tx._expand_trace.call_count
    tx.source(-5)
    assert tx._expand_trace.call_count


def test_info(console_mode, tester):
    """calling for info only evaluates the trace on a reverted tx"""
    tx = tester.doNothing()
    tx.info()
    assert not tx._get_trace.call_count
    assert not tx._expand_trace.call_count
    tx = tester.revertStrings(1)
    tx.info()
    assert tx._get_trace.call_count
    assert not tx._expand_trace.call_count


def test_call_trace(console_mode, tester):
    """call_trace always evaluates the trace"""
    tx = tester.doNothing()
    tx.call_trace()
    assert tx._get_trace.call_count
    assert tx._expand_trace.call_count
    tx = tester.revertStrings(1)
    tx.call_trace()
    assert tx._get_trace.call_count == 2
    assert tx._expand_trace.call_count == 2


def test_trace_deploy(tester):
    """trace is calculated for deploying contracts but not expanded"""
    assert tester.tx.trace
    assert "fn" not in tester.tx.trace[0]


def test_trace_transfer(accounts):
    """trace is not calculated for regular transfers of eth"""
    tx = accounts[0].transfer(accounts[1], "1 ether")
    assert not tx.trace


def test_expand_first(tester):
    """can call _expand_trace without _get_trace first"""
    tx = tester.doNothing()
    assert not tx._get_trace.call_count
    assert not tx._expand_trace.call_count
    tx._expand_trace()
    assert tx._get_trace.call_count


def test_expand_multiple(tester):
    """multiple calls to get_trace and expand_trace should not raise"""
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
    tx._revert_msg = None
    tx._reverted_trace(tx.trace)
    assert tx.revert_msg == msg


def test_inlined_library_jump(accounts, tester):
    tx = tester.useSafeMath(6, 7)
    assert max([i["jumpDepth"] for i in tx.trace]) == 1


def test_internal_jumps(accounts, testproject, tester):
    tx = tester.makeInternalCalls(False, True)
    assert max([i["depth"] for i in tx.trace]) == 0
    assert max([i["jumpDepth"] for i in tx.trace]) == 1
    tx = tester.makeInternalCalls(True, False)
    assert max([i["depth"] for i in tx.trace]) == 0
    assert max([i["jumpDepth"] for i in tx.trace]) == 2
    tx = tester.makeInternalCalls(True, True)
    assert max([i["depth"] for i in tx.trace]) == 0
    assert max([i["jumpDepth"] for i in tx.trace]) == 2
    tx.call_trace()


def test_external_jump(accounts, tester, ext_tester):
    tx = tester.makeExternalCall(ext_tester, 4)
    assert max([i["depth"] for i in tx.trace]) == 1
    assert max([i["jumpDepth"] for i in tx.trace]) == 0


def test_external_jump_to_self(accounts, testproject, tester):
    tx = tester.makeExternalCall(tester, 0)
    assert max([i["depth"] for i in tx.trace]) == 1
    assert max([i["jumpDepth"] for i in tx.trace]) == 1
    tx.call_trace()


def test_delegatecall_jump(accounts, librarytester):
    accounts[0].deploy(librarytester["TestLib"])
    contract = accounts[0].deploy(librarytester["Unlinked"])
    tx = contract.callLibrary(6, 7)
    assert max([i["depth"] for i in tx.trace]) == 1
    assert max([i["jumpDepth"] for i in tx.trace]) == 0


def test_unknown_contract(ExternalCallTester, accounts, tester, ext_tester):
    tx = tester.makeExternalCall(ext_tester, 4)
    del ExternalCallTester[0]
    tx.call_trace()


def test_contractabi(ExternalCallTester, accounts, tester, ext_tester):
    tx = tester.makeExternalCall(ext_tester, 4)
    del ExternalCallTester[0]
    ext_tester = Contract.from_abi("ExternalTesterABI", ext_tester.address, ext_tester.abi)
    tx.call_trace()


def test_traces_not_supported(network, chain):
    network.connect("goerli")

    # this tx reverted
    tx = chain.get_transaction("0xbb75b5cccc0c009f2073097252e76a1f8452ba6b3b7c5a5837c59a37bfaee305")

    # the confirmation output should work even without traces
    tx._confirm_output()

    # querying the revert message should raise
    with pytest.raises(RPCRequestError):
        tx.revert_msg
