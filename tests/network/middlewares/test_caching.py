#!/usr/bin/python3

import threading

from brownie.network.middlewares.caching import RequestCachingMiddleware


class _DisconnectedWeb3:
    def isConnected(self):
        return False


def test_uninstall_wakes_cache_middleware_sleep():
    middleware = object.__new__(RequestCachingMiddleware)
    middleware.is_killed = False
    middleware._sleep_event = threading.Event()
    middleware.block_cache = {}
    middleware.block_filter = None
    middleware.w3 = _DisconnectedWeb3()

    woke = threading.Event()
    started = threading.Event()

    def wait_for_sleep_event():
        started.set()
        middleware._sleep_event.wait(5)
        woke.set()

    thread = threading.Thread(target=wait_for_sleep_event)
    thread.start()
    assert started.wait(1)
    assert not woke.is_set()

    middleware.uninstall()

    assert middleware.is_killed is True
    assert middleware._sleep_event.is_set()
    assert woke.wait(1)
    thread.join(1)
