#!/usr/bin/python3

import time
from threading import Thread


RED = "\033[91m"
DEFAULT = "\x1b[0m"

_instances = set()

class Alert:

    def __init__(self, fn, args=[], kwargs={}, delay=0.5, msg=None, callback=None):
        if not callable(fn):
            raise TypeError("You can only set an alert on a callable object")
        self._kill = False
        self._thread = Thread(
            target=self._loop, daemon=True,
            args=(fn, args, kwargs, delay, msg, callback))
        self._thread.start()
        _instances.add(self)
        
    def _loop(self, fn, args, kwargs, delay, msg, callback):
        start_value = fn(*args, **kwargs)
        while not self._kill:
            time.sleep(delay)
            value = fn(*args, **kwargs)
            if value == start_value:
                continue
            if msg:
                msg = msg.format(start_value, value)
                print("{}ALERT{}: {}".format(RED, DEFAULT, msg))
            if callback:
                callback(start_value, value)
            _instances.discard(self)
            return

    def stop(self):
        self._kill = True
        self._thread.join()
        _instances.discard(self)

def new(fn, args=[], kwargs={}, delay=0.5, msg=None, callback=None):
    return Alert(fn, args, kwargs, delay, msg, callback)

def show():
    return list(_instances)

def stop_all():
    for t in _instances.copy():
        t.stop()