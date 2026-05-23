#!/usr/bin/python3


import time

import pytest


def _wait_for_undo_buffer(chain, size):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if chain._undo_lock.acquire(timeout=0.1):
            try:
                if len(chain._undo_buffer) >= size:
                    return
            finally:
                chain._undo_lock.release()
        time.sleep(0.01)
    pytest.fail(f"Undo buffer did not reach {size} entries")


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


def test_sleep_zero_preserves_redo_buffer(accounts, chain, web3):
    accounts[0].transfer(accounts[1], 100)
    accounts[0].transfer(accounts[1], 100)
    _wait_for_undo_buffer(chain, 2)
    chain.undo()
    height_after_undo = web3.eth.block_number

    with chain._undo_lock:
        undo_depth = len(chain._undo_buffer)
        redo_depth = len(chain._redo_buffer)
        current_id = chain._current_id

    chain.sleep(0)

    with chain._undo_lock:
        assert len(chain._undo_buffer) == undo_depth
        assert len(chain._redo_buffer) == redo_depth
        assert chain._current_id == current_id

    chain.redo()
    _wait_for_undo_buffer(chain, undo_depth + 1)
    assert web3.eth.block_number == height_after_undo + 1
    chain.undo()
    assert web3.eth.block_number == height_after_undo


def test_mine_clears_redo_buffer(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    accounts[0].transfer(accounts[1], 100)
    chain.undo()
    chain.mine()
    with pytest.raises(ValueError):
        chain.redo()
