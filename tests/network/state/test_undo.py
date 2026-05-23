#!/usr/bin/python3

import threading
import time

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
    lock = _block_first_undo_lock(chain, monkeypatch)
    accounts[0].transfer(accounts[1], 100)
    assert lock.blocked.wait(5)

    sleep_seconds = 100000
    start_time = chain.time()
    thread, thread_errors = _run_in_thread(lambda: chain.sleep(sleep_seconds))
    lock.release_block.set()

    _assert_thread_finished(thread, thread_errors)
    assert not lock.errors, lock.errors[0]

    accounts[0].transfer(accounts[1], 100)
    _wait_for_undo_buffer(chain, 2)
    chain.undo()
    assert chain.time() >= start_time + sleep_seconds - 5


def test_mine_waits_for_pending_undo_registration(accounts, chain, web3, monkeypatch):
    lock = _block_first_undo_lock(chain, monkeypatch)
    accounts[0].transfer(accounts[1], 100)
    assert lock.blocked.wait(5)

    thread, thread_errors = _run_in_thread(chain.mine)
    lock.release_block.set()

    _assert_thread_finished(thread, thread_errors)
    assert not lock.errors, lock.errors[0]

    mined_height = web3.eth.block_number
    accounts[0].transfer(accounts[1], 100)
    _wait_for_undo_buffer(chain, 2)
    chain.undo()
    assert web3.eth.block_number == mined_height


class _BlockingUndoLock:
    def __init__(self, lock):
        self._lock = lock
        self.blocked = threading.Event()
        self.release_block = threading.Event()
        self.errors = []
        self._block_next_acquire = True

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.release()

    def acquire(self, *args, **kwargs):
        acquired = self._lock.acquire(*args, **kwargs)
        if acquired and self._block_next_acquire:
            self._block_next_acquire = False
            self.blocked.set()
            if not self.release_block.wait(5):
                self.errors.append(TimeoutError("timed out releasing undo lock"))
        return acquired

    def release(self):
        self._lock.release()


def _block_first_undo_lock(chain, monkeypatch):
    lock = _BlockingUndoLock(chain._undo_lock)
    monkeypatch.setattr(chain, "_undo_lock", lock)
    return lock


def _wait_for_undo_buffer(chain, size):
    if not chain._undo_lock.blocked.wait(5):
        pytest.fail("Undo registration did not acquire the undo lock")

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
