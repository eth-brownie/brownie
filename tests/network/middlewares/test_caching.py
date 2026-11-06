#!/usr/bin/python3

import threading
from collections import OrderedDict

import pytest
from web3 import Web3

from brownie.network.middlewares.caching import RequestCachingMiddleware


class _DisconnectedWeb3(Web3):
    def isConnected(self):
        return False


@pytest.fixture
def middleware(config, monkeypatch):
    original_network = config._active_network
    config._active_network = {"chainid": "1"}
    w3 = _DisconnectedWeb3()

    def raise_before_initialization(*args):
        raise RuntimeError("boom")

    monkeypatch.setattr(w3.eth, "get_block", raise_before_initialization)
    instance = RequestCachingMiddleware(w3)
    try:
        yield instance
    finally:
        instance.uninstall()
        config._active_network = original_network


def test_uninstall_stops_waiting_filter_thread(middleware):
    middleware.is_killed = False
    middleware.event.clear()
    middleware._stop_event.clear()
    middleware.block_cache = OrderedDict({"block": {}})
    middleware.block_filter = object()

    started = threading.Event()

    def wait_for_event():
        started.set()
        middleware.event.wait(5)

    middleware.loop_thread = threading.Thread(target=wait_for_event)
    middleware.loop_thread.start()
    assert started.wait(1)
    assert middleware.loop_thread.is_alive()

    middleware.uninstall()

    assert middleware.is_killed is True
    assert middleware._stop_event.is_set()
    assert middleware.event.is_set()
    assert middleware.block_cache == {}
    assert not middleware.loop_thread.is_alive()


def test_uninstall_does_not_join_current_thread(middleware):
    middleware.is_killed = False
    middleware.event.clear()
    middleware._stop_event.clear()
    middleware.block_cache = OrderedDict()
    middleware.block_filter = None
    middleware.loop_thread = threading.current_thread()

    middleware.uninstall()

    assert middleware.is_killed is True
    assert middleware._stop_event.is_set()
    assert middleware.event.is_set()


def test_loop_exception_handler_releases_startup_waiters(middleware):
    assert middleware.is_killed is True
    assert middleware.event.is_set()
