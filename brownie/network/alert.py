#!/usr/bin/python3

import time as _time
from threading import Thread as _Thread

from brownie.cli.utils import color as _color

_instances = set()

class Alert:

    '''Setup notifications and callbacks based on state changes to the blockchain.
    The alert is immediatly active as soon as the class is insantiated.'''
    
    def __init__(self, fn, args=[], kwargs={}, delay=0.5, msg=None, callback=None):
        '''Creates a new Alert.

        Args:
            fn: Callable to monitor for changes.
            args: Positional args when checking the callable.
            kwargs: Keyword args when checking the callable.
            delay: Frequency to check for changes, in seconds.
            msg: Notification string to display on change.
            callback: Callback function to call upon change. It must accept two
                      arguments: initial value, new value
        '''
        if not callable(fn):
            raise TypeError("You can only set an alert on a callable object")
        self._kill = False
        self._thread = _Thread(
            target=self._loop, daemon=True,
            args=(fn, args, kwargs, delay, msg, callback))
        self._thread.start()
        _instances.add(self)
        
    def _loop(self, fn, args, kwargs, delay, msg, callback):
        start_value = fn(*args, **kwargs)
        while not self._kill:
            _time.sleep(delay)
            value = fn(*args, **kwargs)
            if value == start_value:
                continue
            if msg:
                msg = msg.format(start_value, value)
                print("{0[bright red]}ALERT{0}: {1}".format(_color, msg))
            if callback:
                callback(start_value, value)
            _instances.discard(self)
            return

    def stop(self):
        '''Stops the alert'''
        self._kill = True
        self._thread.join()
        _instances.discard(self)

def new(fn, args=[], kwargs={}, delay=0.5, msg=None, callback=None):
    '''Alias for creating a new Alert instance.'''
    return Alert(fn, args, kwargs, delay, msg, callback)

def show():
    '''Returns a list of all currently active Alert instances.'''
    return list(_instances)

def stop_all():
    '''Stops all currently active Alert instances.'''
    for t in _instances.copy():
        t.stop()