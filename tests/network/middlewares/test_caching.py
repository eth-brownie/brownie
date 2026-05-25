#!/usr/bin/python3

import threading

from brownie.network.middlewares.caching import RequestCachingMiddleware


class _DisconnectedWeb3:
    def isConnected(self):
        return False


def test_uninstall_stops_waiting_filter_thread():
    middleware = object.__new__(RequestCachingMiddleware)
    middleware.is_killed = False
    middleware.event = threading.Event()
    middleware._stop_event = threading.Event()
    middleware.block_cache = {"block": {}}
    middleware.block_filter = object()
    middleware.w3 = _DisconnectedWeb3()

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


def test_uninstall_does_not_join_current_thread():
    middleware = object.__new__(RequestCachingMiddleware)
    middleware.is_killed = False
    middleware.event = threading.Event()
    middleware._stop_event = threading.Event()
    middleware.block_cache = {}
    middleware.block_filter = None
    middleware.loop_thread = threading.current_thread()
    middleware.w3 = _DisconnectedWeb3()

    middleware.uninstall()

    assert middleware.is_killed is True
    assert middleware._stop_event.is_set()
    assert middleware.event.is_set()


def test_loop_exception_handler_releases_startup_waiters():
    middleware = object.__new__(RequestCachingMiddleware)
    middleware.event = threading.Event()
    middleware.is_killed = False

    def raise_before_initialization():
        raise RuntimeError("boom")

    middleware.block_filter_loop = raise_before_initialization

    middleware.loop_exception_handler()

    assert middleware.is_killed is True
    assert middleware.event.is_set()
