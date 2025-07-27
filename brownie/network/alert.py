#!/usr/bin/python3

import time
from threading import Thread
from typing import Callable, Dict, Final, List, Optional, Set, Tuple, Union

from mypy_extensions import mypyc_attr

from brownie.utils import bright_red, color

__console_dir__: Final = ["Alert", "new", "show", "stop_all"]
_instances: Final[Set["Alert"]] = set()

# Internal C Constants

_Thread: Final = Thread

_sleep: Final = time.sleep
_time: Final = time.time


@mypyc_attr(native_class=False)
# TODO: remove this decorator once the compiler bug preventing compilation is fixed
class Alert:
    """Setup notifications and callbacks based on state changes to the blockchain.
    The alert is immediatly active as soon as the class is insantiated."""

    def __init__(
        self,
        fn: Callable,
        args: Optional[Tuple] = None,
        kwargs: Optional[Dict] = None,
        delay: float = 2,
        msg: Optional[str] = None,
        callback: Optional[Callable] = None,
        repeat: bool = False,
    ) -> None:
        """Creates a new Alert.
        Args:
            fn: Callable to monitor for changes.
            args: Positional args when checking the callable.
            kwargs: Keyword args when checking the callable.
            delay: Frequency to check for changes, in seconds.
            msg: Notification string to display on change.
            callback: Callback function to call upon change. It must accept two
                      arguments: initial value, new value
            repeat: if False, the alert will terminate after firing once.
                    if True, the alert will continue to fire on changes until it
                    is terminated via Alert.stop()
                    if int, the alert will fire n+1 times before terminating.
        """
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        if not callable(fn):
            raise TypeError("You can only set an alert on a callable object")
        if isinstance(repeat, int) and repeat < 0:
            raise ValueError("repeat must be True, False or a positive integer")
        self._kill: bool = False
        start_value = fn(*args, **kwargs)
        self._thread: Final = _Thread(
            target=self._loop,
            daemon=True,
            args=(fn, args, kwargs, start_value, delay, msg, callback, repeat),
        )
        self._thread.start()
        self.start_time: Final = _time()
        _instances.add(self)

    def _loop(
        self,
        fn: Callable,
        args: Tuple,
        kwargs: Dict,
        start_value: int,
        delay: float,
        msg: str,
        callback: Callable,
        repeat: Union[int, bool, None] = False,
    ) -> None:
        try:
            sleep = min(delay, 0.05)
            while repeat is not None:
                next_ = _time() + delay
                while next_ > _time() and not self._kill:
                    _sleep(sleep)
                if self._kill:
                    break
                value = fn(*args, **kwargs)
                if value == start_value:
                    continue
                if msg:
                    fmt_msg = msg.format(start_value, value)
                    print(f"{bright_red}ALERT{color}: {fmt_msg}")
                if callback is not None:
                    callback(start_value, value)
                start_value = value
                if not repeat:
                    repeat = None
                elif isinstance(repeat, int) and not isinstance(repeat, bool):
                    repeat -= 1
        finally:
            _instances.discard(self)

    def is_alive(self) -> bool:
        """Checks if the alert is currently active."""
        return self._thread.is_alive()

    def wait(self, timeout: Optional[int] = None) -> None:
        """Waits for the alert to fire.
        Args:
            timeout: Number of seconds to wait. If None, will wait indefinitely."""
        self._thread.join(timeout)

    def stop(self, wait: bool = True) -> None:
        """Stops the alert.
        Args:
            wait: If True, waits for the alert to terminate after stopping it."""
        self._kill = True
        if wait:
            self.wait()
    
    def _get_start_time(self) -> float:
        """Internal helper for use as a sort key."""
        return self.start_time


def new(
    fn: Callable,
    args: Optional[Tuple] = None,
    kwargs: Optional[Dict] = None,
    delay: float = 0.5,
    msg: Optional[str] = None,
    callback: Optional[Callable] = None,
    repeat: bool = False,
) -> "Alert":
    """Alias for creating a new Alert instance."""
    return Alert(fn, args, kwargs, delay, msg, callback, repeat)


def show() -> List[Alert]:
    """Returns a list of all currently active Alert instances."""
    return sorted(_instances, key=Alert._get_start_time)


def stop_all() -> None:
    """Stops all currently active Alert instances."""
    for t in _instances.copy():
        t.stop()
    _instances.clear()
