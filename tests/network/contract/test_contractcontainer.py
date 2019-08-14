#!/usr/bin/python3

import pytest


def test_get_method(BrownieTester):
    calldata = "0x2e27149600000000000000000000000066ab6d9362d4f35596279692f0251db635165871"
    assert BrownieTester.get_method(calldata) == "getTuple"


def test_container(BrownieTester, accounts, rpc):
    assert len(BrownieTester) == 0
    t = BrownieTester.deploy(True, {'from': accounts[0]})
    t2 = BrownieTester.deploy(True, {'from': accounts[0]})
    assert len(BrownieTester) == 2
    assert BrownieTester[0] == t
    assert BrownieTester[1] == t2
    assert list(BrownieTester) == [t, t2]
    assert t in BrownieTester
    del BrownieTester[0]
    assert len(BrownieTester) == 1
    assert BrownieTester[0] == t2
    rpc.reset()
    assert len(BrownieTester) == 0


def test_remove_at(BrownieTester, accounts):
    t = BrownieTester.deploy(True, {'from': accounts[0]})
    BrownieTester.remove(t)
    assert len(BrownieTester) == 0
    assert BrownieTester.at(t.address) == t
    assert len(BrownieTester) == 1
    t2 = BrownieTester.deploy(True, {'from': accounts[0]})
    BrownieTester.remove(t2)
    with pytest.raises(TypeError):
        BrownieTester.remove(t2)
    with pytest.raises(TypeError):
        BrownieTester.remove(123)


def test_load_unload_project(BrownieTester, testproject, rpc, accounts):
    BrownieTester.deploy(True, {'from': accounts[0]})
    testproject.close()
    rpc.reset()
    assert len(BrownieTester) == 0
    testproject.load()
    assert testproject.BrownieTester != BrownieTester
