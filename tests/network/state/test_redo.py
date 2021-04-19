#!/usr/bin/python3


import pytest


def test_redo(accounts, chain, web3):
    accounts[0].transfer(accounts[1], "1 ether")
    result = accounts[0].balance()
    chain.undo()
    chain.redo()
    assert web3.eth.block_number == 1
    assert accounts[0].balance() == result


def test_redo_multiple(accounts, chain, web3):
    for i in range(1, 6):
        accounts[0].transfer(accounts[i], f"{i} ether")
    result = accounts[0].balance()
    chain.undo(5)
    chain.redo(5)
    assert accounts[0].balance() == result


def test_redo_contract_tx(tester, accounts, chain, history):
    tester.receiveEth({"from": accounts[0], "amount": "1 ether"})
    chain.undo()
    chain.redo()
    assert history[-1].fn_name == "receiveEth"


def test_redo_deploy(BrownieTester, accounts, chain):
    BrownieTester.deploy(True, {"from": accounts[0]})
    chain.undo()
    chain.redo()
    assert len(BrownieTester) == 1


def test_redo_empty_buffer(accounts, chain):
    with pytest.raises(ValueError):
        chain.redo()


def test_redo_zero(accounts, chain):
    with pytest.raises(ValueError):
        chain.redo(0)


def test_redo_too_many(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    accounts[0].transfer(accounts[1], 100)
    chain.undo()
    with pytest.raises(ValueError):
        chain.redo(2)


def test_snapshot_clears_redo_buffer(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    accounts[0].transfer(accounts[1], 100)
    chain.undo()
    chain.snapshot()
    with pytest.raises(ValueError):
        chain.redo()


def test_revert_clears_redo_buffer(accounts, chain):
    chain.snapshot()
    accounts[0].transfer(accounts[1], 100)
    accounts[0].transfer(accounts[1], 100)
    chain.undo()
    chain.revert()
    with pytest.raises(ValueError):
        chain.redo()


def test_sleep_clears_redo_buffer(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    accounts[0].transfer(accounts[1], 100)
    chain.undo()
    chain.sleep(100)
    with pytest.raises(ValueError):
        chain.redo()


def test_mine_clears_redo_buffer(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    accounts[0].transfer(accounts[1], 100)
    chain.undo()
    chain.mine()
    with pytest.raises(ValueError):
        chain.redo()
