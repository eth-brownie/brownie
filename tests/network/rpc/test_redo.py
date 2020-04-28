#!/usr/bin/python3


import pytest


def test_redo(accounts, rpc, web3):
    accounts[0].transfer(accounts[1], "1 ether")
    result = accounts[0].balance()
    rpc.undo()
    rpc.redo()
    assert web3.eth.blockNumber == 1
    assert accounts[0].balance() == result


def test_redo_multiple(accounts, rpc, web3):
    for i in range(1, 6):
        accounts[0].transfer(accounts[i], "1 ether")
    result = accounts[0].balance()
    rpc.undo(5)
    rpc.redo(5)
    assert accounts[0].balance() == result


def test_redo_contract_tx(tester, accounts, rpc, history):
    tester.receiveEth({"from": accounts[0], "amount": "1 ether"})
    rpc.undo()
    rpc.redo()
    assert history[-1].fn_name == "receiveEth"


def test_redo_deploy(BrownieTester, accounts, rpc):
    BrownieTester.deploy(True, {"from": accounts[0]})
    rpc.undo()
    rpc.redo()
    assert len(BrownieTester) == 1


def test_redo_empty_buffer(accounts, rpc):
    with pytest.raises(ValueError):
        rpc.redo()


def test_redo_zero(accounts, rpc):
    with pytest.raises(ValueError):
        rpc.redo(0)


def test_redo_too_many(accounts, rpc):
    accounts[0].transfer(accounts[1], 100)
    accounts[0].transfer(accounts[1], 100)
    rpc.undo()
    with pytest.raises(ValueError):
        rpc.redo(2)


def test_snapshot_clears_redo_buffer(accounts, rpc):
    accounts[0].transfer(accounts[1], 100)
    accounts[0].transfer(accounts[1], 100)
    rpc.undo()
    rpc.snapshot()
    with pytest.raises(ValueError):
        rpc.redo()


def test_revert_clears_undo_buffer(accounts, rpc):
    rpc.snapshot()
    accounts[0].transfer(accounts[1], 100)
    accounts[0].transfer(accounts[1], 100)
    rpc.undo()
    rpc.revert()
    with pytest.raises(ValueError):
        rpc.redo()
