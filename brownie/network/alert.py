#!/usr/bin/python3

import asyncio
import time as time
from threading import Lock, Thread
from typing import Callable, Dict, List, Tuple, Union

from web3._utils import filters
from web3.datastructures import AttributeDict

from brownie.utils import color

from .web3 import ContractEvent, web3

__console_dir__ = ["Alert", "new", "show", "stop_all"]
_instances = set()


class Alert:

    """Setup notifications and callbacks based on state changes to the blockchain.
    The alert is immediatly active as soon as the class is insantiated."""

    def __init__(
        self,
        fn: Callable,
        args: Tuple = None,
        kwargs: Dict = None,
        delay: float = 2,
        msg: str = None,
        callback: Callable = None,
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
        self._kill = False
        start_value = fn(*args, **kwargs)
        self._thread = Thread(
            target=self._loop,
            daemon=True,
            args=(fn, args, kwargs, start_value, delay, msg, callback, repeat),
        )
        self._thread.start()
        self.start_time = time.time()
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
                next_ = time.time() + delay
                while next_ > time.time() and not self._kill:
                    time.sleep(sleep)
                if self._kill:
                    break
                value = fn(*args, **kwargs)
                if value == start_value:
                    continue
                if msg:
                    fmt_msg = msg.format(start_value, value)
                    print(f"{color('bright red')}ALERT{color}: {fmt_msg}")
                if callback:
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

    def wait(self, timeout: int = None) -> None:
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


class EventWatchData:
    def __init__(
        self,
        event: ContractEvent,
        callback: Callable[[AttributeDict], None],
        delay: float = 2.0,
        repeat: bool = True,
        from_block: int = None,
    ) -> None:
        # Args
        self.event = event
        self.callback = callback
        self.delay = delay
        self.repeat = repeat
        # Members
        self._event_filter: filters.LogFilter = event.createFilter(
            fromBlock=(from_block if from_block is not None else web3.eth.block_number - 1)
        )
        self._cooldown_time_over: bool = False
        self._update_trigger_time()

    def check_timer(self) -> float:
        current_time: float = time.time()
        time_since_last_trigger: float = current_time - self.last_trigger_time
        # Sets callback execution as ready when timer is greater than delay
        if time_since_last_trigger >= self.delay:
            self.cooldown_time_over = True
        # Return time left on watch in seconds
        return self.delay - time_since_last_trigger

    def get_new_events(self):
        return self._event_filter.get_new_entries()

    def _trigger_callback(self, events_data: List[AttributeDict]):
        self.cooldown_time_over = False
        self._update_trigger_time()
        for data in events_data:
            self.callback(data)

    def _update_trigger_time(self):
        self.last_trigger_time: float = time.time()

    def cd_time_over_getter(self) -> bool:
        current_time = time.time()
        timer_value = current_time - self.last_trigger_time
        if timer_value >= self.delay:
            self._cooldown_time_over = True
        return self._cooldown_time_over

    def cd_time_over_setter(self, value: bool):
        self._cooldown_time_over = value

    cooldown_time_over = property(fget=cd_time_over_getter, fset=cd_time_over_setter)


class EventWatcher:
    def __init__(self):
        self.target_list_lock: Lock = Lock()
        self.target_events_watch_data: List[EventWatchData] = []
        self._queue: asyncio.Queue = asyncio.Queue()
        self._kill: bool = False
        self._has_started: bool = False
        self._watcher_thread = Thread(target=self._watch_loop, daemon=True)
        self._callback_thread = Thread(target=self._execute_callbacks, daemon=True)

    def start(self):
        # Starts two new Thread running the _watch_loop and the _execute_callbacks method.
        self._watcher_thread.start()
        self._callback_thread.start()
        self._has_started = True

    def stop(self, wait: bool = True):
        self._kill = True
        if wait is True:
            self._watcher_thread.join()

    def add_event_callback(
        self,
        event: ContractEvent,
        callback: Callable[[AttributeDict], None],
        delay: float = 2.0,
        repeat: bool = True,
        from_block: int = None,
    ):
        if self._has_started is False:
            self.start()
        self._add_event_callback(event, callback, delay, repeat, from_block)

    def _add_event_callback(
        self,
        event: ContractEvent,
        callback: Callable[[AttributeDict], None],
        delay: float = 2.0,
        repeat: bool = True,
        from_block: int = None,
    ):
        if not callable(callback):
            raise TypeError("Argument 'callback' argument must be a callable.")
        delay = max(delay, 0.05)
        self.target_list_lock.acquire()  # lock
        self.target_events_watch_data.append(
            EventWatchData(event, callback, delay, repeat, from_block)
        )
        self.target_list_lock.release()  # unlock

    def _execute_callbacks(self):
        while not self._kill:
            try:
                # print("Checking for callbacks...")
                # print("[EXECUTER] - Executing events...")
                while self._queue.qsize() > 0:
                    task_data = self._queue.get_nowait()
                    # Execute callbacks with new events data
                    task_data["function"](task_data["events_data"])
                    # print(
                    #     f"[EXECUTER] - Executing callback with events data
                    # list of size : {len(task_data['events_data'])}"
                    # )
            except asyncio.QueueEmpty:
                pass
            # print("[EXECUTER] - Done checking, taking a nap...")
            time.sleep(5.0)

    def _watch_loop(self):
        while not self._kill:
            try:
                print("[WATCHER] - Awake ! Checking...")
                sleep_time: float = 2.0  # Max sleep time.
                self.target_list_lock.acquire()  # lock
                for elem in self.target_events_watch_data:
                    # print(f"[WATCHER] - Watching event {elem.event.event_name}")
                    # If cooldown is not over, skip.
                    if elem.cooldown_time_over is False:
                        sleep_time = min(sleep_time, elem.check_timer())
                        continue
                    # print("[WATCHER] - Cooldown reached ! Checking for new events.")
                    # Check for new events & execute callback async if some are found
                    latest_events = elem.get_new_events()
                    if len(latest_events) != 0:
                        # print(f"[WATCHER] - New events detected :
                        # {len(latest_events)}, adding callback to queue.")
                        self._queue.put(
                            {
                                "function": elem._trigger_callback,
                                "events_data": latest_events,
                            }
                        )
                    sleep_time = min(sleep_time, elem.delay)
            finally:
                self.target_list_lock.release()  # unlock
                print(f"[WATCHER] - Checked ! Sleeping for {sleep_time} seconds ...")
                time.sleep(sleep_time)
                # print(f"[WATCHER] - Loop is alive : {not self._kill}")
        # print("[WATCHER] - Leaving watch loop.")


def new(
    fn: Callable,
    args: Tuple = None,
    kwargs: Dict = None,
    delay: float = 0.5,
    msg: str = None,
    callback: Callable = None,
    repeat: bool = False,
) -> "Alert":
    """Alias for creating a new Alert instance."""
    return Alert(fn, args, kwargs, delay, msg, callback, repeat)


def show() -> List:
    """Returns a list of all currently active Alert instances."""
    return sorted(_instances, key=lambda k: k.start_time)


def stop_all() -> None:
    """Stops all currently active Alert instances."""
    for t in _instances.copy():
        t.stop()
    _instances.clear()


event_watcher = EventWatcher()
