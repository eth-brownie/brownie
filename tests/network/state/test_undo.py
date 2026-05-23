#!/usr/bin/python3

import threading

import pytest


def test_undo(accounts, chain, web3):
    initial = accounts[0].balance()
    accounts[0].transfer(accounts[1], "1 ether")
    chain.undo()
    assert web3.eth.block_number == 0
    assert accounts[0].balance() == initial


def test_undo_multiple(accounts, chain, web3):
    initial = accounts[0].balance()
    for i in range(1, 6):
        accounts[0].transfer(accounts[i], f"{i} ether")
    chain.undo(5)
    assert accounts[0].balance() == initial


def test_undo_empty_buffer(accounts, chain):
    with pytest.raises(ValueError):
        chain.undo()


def test_undo_zero(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    with pytest.raises(ValueError):
        chain.undo(0)


def test_undo_too_many(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    with pytest.raises(ValueError):
        chain.undo(2)


def test_snapshot_clears_undo_buffer(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    chain.snapshot()
    with pytest.raises(ValueError):
        chain.undo()


def test_revert_clears_undo_buffer(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    chain.snapshot()
    accounts[0].transfer(accounts[1], 100)
    chain.revert()
    with pytest.raises(ValueError):
        chain.undo()


def test_does_not_undo_sleep(accounts, chain):
    accounts[0].transfer(accounts[1], 100)
    time = chain.time()
    chain.sleep(100000)
    accounts[0].transfer(accounts[1], 100)
    chain.undo()
    assert chain.time() >= time + 100000


def test_does_not_undo_mining(accounts, chain, web3):
    accounts[0].transfer(accounts[1], 100)
    chain.mine()
    height = web3.eth.block_number
    accounts[0].transfer(accounts[1], 100)
    chain.undo()
    assert web3.eth.block_number == height


def test_sleep_waits_for_pending_undo_registration(accounts, chain, monkeypatch):
    blocked, release, first_done, second_done, errors = _block_first_undo_registration(
        chain, monkeypatch
    )
    accounts[0].transfer(accounts[1], 100)
    assert blocked.wait(5)

    sleep_seconds = 100000
    start_time = chain.time()
    thread, thread_errors = _run_in_thread(lambda: chain.sleep(sleep_seconds))
    release.set()

    _assert_thread_finished(thread, thread_errors)
    assert first_done.wait(5)
    assert not errors, errors[0]

    accounts[0].transfer(accounts[1], 100)
    assert second_done.wait(5)
    chain.undo()
    assert chain.time() >= start_time + sleep_seconds - 5


def test_mine_waits_for_pending_undo_registration(accounts, chain, web3, monkeypatch):
    blocked, release, first_done, second_done, errors = _block_first_undo_registration(
        chain, monkeypatch
    )
    accounts[0].transfer(accounts[1], 100)
    assert blocked.wait(5)

    thread, thread_errors = _run_in_thread(chain.mine)
    release.set()

    _assert_thread_finished(thread, thread_errors)
    assert first_done.wait(5)
    assert not errors, errors[0]

    mined_height = web3.eth.block_number
    accounts[0].transfer(accounts[1], 100)
    assert second_done.wait(5)
    chain.undo()
    assert web3.eth.block_number == mined_height


def _block_first_undo_registration(chain, monkeypatch):
    original = chain._add_to_undo_buffer_unlocked
    blocked = threading.Event()
    release = threading.Event()
    first_done = threading.Event()
    second_done = threading.Event()
    errors = []
    calls = 0

    def controlled(tx, fn, args, kwargs):
        nonlocal calls
        calls += 1
        is_first = calls == 1
        if is_first:
            tx._confirmed.wait()
            blocked.set()
            if not release.wait(5):
                errors.append(TimeoutError("timed out releasing undo registration"))
                return

        original(tx, fn, args, kwargs)

        if is_first:
            first_done.set()
        else:
            second_done.set()

    monkeypatch.setattr(chain, "_add_to_undo_buffer_unlocked", controlled)
    return blocked, release, first_done, second_done, errors


def _run_in_thread(fn):
    started = threading.Event()
    errors = []

    def target():
        started.set()
        try:
            fn()
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    assert started.wait(5)
    return thread, errors


def _assert_thread_finished(thread, errors):
    thread.join(5)
    assert not thread.is_alive()
    assert not errors, errors[0]
