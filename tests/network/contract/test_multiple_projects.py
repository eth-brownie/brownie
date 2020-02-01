#!/usr/bin/python3

import pytest

from brownie.exceptions import ContractExists, VirtualMachineError


def test_deploy(BrownieTester, otherproject, accounts):
    t = BrownieTester.deploy(True, {"from": accounts[0]})
    assert len(BrownieTester) == 1
    assert len(otherproject.BrownieTester) == 0
    assert t not in otherproject.BrownieTester
    t2 = otherproject.BrownieTester.deploy(True, {"from": accounts[0]})
    assert len(BrownieTester) == 1
    assert len(otherproject.BrownieTester) == 1
    assert t2 not in BrownieTester


def test_at_remove(BrownieTester, otherproject, accounts):
    t = otherproject.BrownieTester.deploy(True, {"from": accounts[0]})
    with pytest.raises(ContractExists):
        BrownieTester.at(t.address)
    otherproject.BrownieTester.remove(t)
    BrownieTester.at(t.address)


def test_interaction(tester, otherproject, accounts):
    ext = otherproject.ExternalCallTester.deploy({"from": accounts[0]})
    tester.makeExternalCall(ext, 42)


def test_revert_strings(tester, otherproject, accounts, history):
    ext = otherproject.ExternalCallTester.deploy({"from": accounts[0]})
    with pytest.raises(VirtualMachineError):
        ext.makeExternalCall(tester, 1)
    assert history[-1].revert_msg == "dev: one"
