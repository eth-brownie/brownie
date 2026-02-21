#!/usr/bin/python3
# mypy: disable-error-code="union-attr"

import time
import warnings
from collections import OrderedDict
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence, ValuesView
from pathlib import Path
from threading import Lock, Thread
from typing import TYPE_CHECKING, Any, Final, Generic, TypeVar, Union, cast, final, overload

import eth_event
from eth_event import EventError
from eth_event.main import DecodedEvent, NonDecodedEvent, TopicMapData, _TraceStep
from eth_typing import ABIElement, AnyAddress, ChecksumAddress, HexStr
from ujson import JSONDecodeError
from web3._utils import filters
from web3.datastructures import AttributeDict

from brownie._c_constants import ujson_dump, ujson_load
from brownie._config import _get_data_folder
from brownie._singleton import _Singleton
from brownie.convert.datatypes import ReturnValue
from brownie.convert.normalize import format_event
from brownie.exceptions import EventLookupError
from brownie.network.web3 import ContractEvent, web3
from brownie.typing import FormattedEvent, Selector
from brownie.utils import hexbytes_to_hexstring

if TYPE_CHECKING:
    from brownie.network.contract import Contract


TopicMap = dict[HexStr, TopicMapData]
DeploymentTopics = dict[ChecksumAddress, TopicMap]

EventData = OrderedDict[str, Any]
"""An OrderedDict which contains the indexed args for a single on-chain event."""


@final
class EventDict:
    """
    Dict/list hybrid container, base class for all events fired in a transaction.
    """

    def __init__(self, events: Iterable[FormattedEvent] | None = None) -> None:
        """Instantiates the class.

        Args:
            events: event data as supplied by eth_event.decode_logs or eth_event.decode_trace"""
        events = list(events) if events else []

        ordered: list[Event] = [
            _EventItem(
                i["name"],
                i["address"],
                [OrderedDict((x["name"], x["value"]) for x in i["data"])],
                (pos,),
            )
            for pos, i in enumerate(events)
        ]
        self._ordered: Final = ordered

        _dict: OrderedDict[str, Events]
        _dict = OrderedDict()
        for event in ordered:
            event_name = event.name
            if event_name not in _dict:
                events_for_name = [i for i in ordered if i.name == event_name]
                _dict[event_name] = _EventItem(
                    event_name,
                    None,
                    events_for_name,
                    tuple(i.pos[0] for i in events_for_name),
                )

        self._dict: Final = _dict

    def __repr__(self) -> str:
        return str(self)

    def __bool__(self) -> bool:
        return bool(self._ordered)

    def __contains__(self, name: str) -> bool:
        """returns True if an event fired with the given name."""
        return name in self._dict

    @overload
    def __getitem__(self, key: int) -> "Event":
        """returns the n'th event that was fired"""

    @overload
    def __getitem__(self, key: str) -> "Events":
        """returns a _EventItem dict of all events where name == key"""

    def __getitem__(self, key: str | int) -> Union["Event", "Events"]:
        """if key is int: returns the n'th event that was fired
        if key is str: returns a _EventItem dict of all events where name == key"""
        if isinstance(key, int):
            try:
                return self._ordered[key]
            except IndexError:
                raise EventLookupError(
                    f"Index out of range - only {len(self._ordered)} events fired"
                ) from None
        elif isinstance(key, str):
            try:
                return self._dict[key]
            except KeyError:
                raise EventLookupError(f"Event '{key}' did not fire.") from None
        else:
            raise TypeError(f"Invalid key type '{type(key)}' - can only use strings or integers")

    def __iter__(self) -> Iterator["Event"]:
        return iter(self._ordered)

    def __len__(self) -> int:
        """returns the number of events that fired."""
        return len(self._ordered)

    def __str__(self) -> str:
        return str({k: [i[0] for i in v._ordered] for k, v in self._dict.items()})

    def count(self, name: str) -> int:
        """EventDict.count(name) -> integer -- return number of occurrences of name"""
        return len(self._dict.get(name, ()))

    def items(self) -> list[tuple[str, "Events"]]:
        """EventDict.items() -> a list object providing a view on EventDict's items"""
        return list(self._dict.items())

    def keys(self) -> list[str]:
        """EventDict.keys() -> a list object providing a view on EventDict's keys"""
        return list(self._dict.keys())

    def values(self) -> ValuesView["Events"]:
        """EventDict.values() -> a list object providing a view on EventDict's values"""
        return self._dict.values()


_TData = TypeVar("_TData", "Event", EventData)


@final
class _EventItem(Generic[_TData]):
    """
    Dict/list hybrid container, represents one or more events with the same name
    that were fired in a transaction.

    Attributes
    ----------
    name : str
        Name of the event.
    address : ChecksumAddress
        Address where this event fired. When the object represents more than one event,
        this value is set to `None`.
    pos : Tuple[int, ...]
        Tuple of indexes where this event fired.
    """

    def __init__(
        self,
        name: str,
        address: ChecksumAddress | None,
        event_data: list[_TData],
        pos: tuple[int, ...],
    ) -> None:
        self.name: Final = name
        self.address: Final = address
        self._ordered: Final = event_data
        self.pos: Final = pos

    @overload
    def __getitem__(self, key: int) -> _TData:
        """returns the n'th event that was fired with this name"""

    @overload
    def __getitem__(self, key: str) -> Any:
        """returns the value of data field 'key' from the 1st event within the container"""

    def __getitem__(self, key: int | str) -> _TData | Any:
        """if key is int: returns the n'th event that was fired with this name
        if key is str: returns the value of data field 'key' from the 1st event
        within the container"""
        if isinstance(key, int):
            try:
                return self._ordered[key]
            except IndexError:
                raise EventLookupError(
                    f"Index out of range - only {len(self._ordered)} '{self.name}' events fired"
                )
        elif isinstance(key, str):
            first = self._ordered[0]
            if key in first:
                return first[key]
            if f"{key} (indexed)" in first:
                return first[f"{key} (indexed)"]
            valid_keys = ", ".join(self.keys())
            raise EventLookupError(
                f"Unknown key '{key}' - the '{self.name}' event includes these keys: {valid_keys}"
            )
        else:
            raise TypeError(f"Invalid key type '{type(key)}' - can only use strings or integers")

    def __contains__(self, name: str) -> bool:
        """returns True if this event contains a value with the given name."""
        return name in self._ordered[0]

    def __len__(self) -> int:
        """returns the number of events held in this container."""
        return len(self._ordered)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        data = self._ordered
        if len(data) == 1:
            return str(data[0])
        return str([i[0] for i in data])  # type: ignore [index]

    def __iter__(self) -> Iterator[_TData]:
        return iter(self._ordered)

    def __eq__(self, other: object) -> bool:
        if len(self._ordered) == 1:
            if isinstance(other, (tuple, list, ReturnValue)):
                # sequences compare directly against the event values
                return self._ordered[0].values() == other
            return other == self._ordered[0]
        return other == self._ordered

    def items(self) -> ReturnValue:
        """_EventItem.items() -> a list object providing a view on _EventItem[0]'s items"""
        return ReturnValue((i, self[i]) for i in self.keys())

    def keys(self) -> ReturnValue:
        """_EventItem.keys() -> a list object providing a view on _EventItem[0]'s keys"""
        return ReturnValue(i.replace(" (indexed)", "") for i in self._ordered[0].keys())

    def values(self) -> ReturnValue:
        """_EventItem.values() -> a list object providing a view on _EventItem[0]'s values"""
        return ReturnValue(self._ordered[0].values())  # type: ignore [arg-type]


Event = _EventItem[EventData]
"""An _EventItem which represents a single event."""

Events = _EventItem[Event]
"""An _EventItem which represents a collection of events which share the same event name."""


@final
class _EventWatchData:
    """
    Class containing the data needed to check, time, and execute callbacks on a specified event.
    """

    def __init__(
        self,
        event: ContractEvent,
        callback: Callable[[AttributeDict], None],
        delay: float = 2.0,
        repeat: bool = True,
    ) -> None:
        # Args
        self.event: Final[ContractEvent] = event
        self._callbacks_list: list[dict] = []
        self.delay: float = delay
        # Members
        self._event_filter: Final[filters.LogFilter] = event.create_filter(
            fromBlock=(web3.eth.block_number - 1)
        )
        self._cooldown_time_over: bool = False
        self.timer = time.time()
        self.add_callback(callback, repeat)

    def get_new_events(self) -> list["filters.LogReceipt"]:
        """
        Retrieves and return the events that occurred between now and the last function call.

        Returns:
            [List[LogReceipt]]: List of the retrieved events
        """
        return self._event_filter.get_new_entries()

    def reset_timer(self) -> None:
        """Resets the 'self.timer' member variable to the current time."""
        self.timer = time.time()

    def add_callback(self, callback: Callable[[AttributeDict], None], repeat: bool = True) -> None:
        """Adds a new callback instruction to execute on new events"""
        if not callable(callback):
            raise TypeError("'callback' argument MUST be a callable object.")
        self._callbacks_list.append({"function": callback, "repeat": repeat})

    def update_delay(self, new_delay: float) -> None:
        """
        Changes the 'delay' member variable if the 'new_delay'
        parameter is inferior to the current one
        """
        self.delay = min(self.delay, new_delay)

    def _trigger_callbacks(self, events_data: list[filters.LogReceipt]) -> list[Thread]:
        """
        Given a list of event as a parameter, creates a thread for each callback
        present in 'self._callbacks_list', stores the thread in a list which is returned.
        Removes non-repeating callbacks from the callback list

        Args:
            events_data (List[AttributeDict]): The list of event to iterate on.
        """

        def _map_callback_on_list(
            callback: Callable, data_to_map: list[filters.LogReceipt]
        ) -> None:
            list(map(callback, data_to_map))

        self.cooldown_time_over = False
        threads: list[Thread] = []
        for callback in self._callbacks_list:
            # Creates a thread for each callback
            threads.append(
                Thread(
                    target=_map_callback_on_list,
                    args=(
                        callback["function"],
                        events_data,
                    ),
                    daemon=True,
                )
            )
            threads[-1].start()
        # Remove non-repeating callbacks from list
        self._callbacks_list = [cb for cb in self._callbacks_list if cb.get("repeat")]
        return threads

    @property
    def time_left(self) -> float:
        """Computes and returns the difference between the self.delay variable
        and the time between now and the last callback_trigger_time.

        Returns:
            float: Time difference between self.delay and the time between
            now and the last callback_trigger_time.
        """
        return max(0.0, self.delay - (time.time() - self.timer))


class EventWatcher(metaclass=_Singleton):
    """
    Singleton class containing methods to set callbacks on user-specified events.
    This class is multi-threaded :
        - The main thread (original process) activates a sub-thread and can be used
        to add callback instructions on specific events.
        - The sub-thread looks for new events among the ones with a callback set.
        When found, calls a method that creates new threads to run the callback
        instructions with the event(s) data as a parameter.
    """

    def __init__(self) -> None:
        self.target_list_lock: Lock = Lock()
        self.target_events_watch_data: dict[str, _EventWatchData] = {}
        self._kill: bool = False
        self._has_started: bool = False
        self._watcher_thread = Thread(target=self._loop, daemon=True)

    def __del__(self) -> None:
        self.stop()

    def stop(self, wait: bool = True) -> None:
        """
        Stops the running threads. This function does not reset the instance
        to its initial state. If that is your goal, check the 'reset' method.

        Args:
            wait (bool, optional): Whether to wait for thread to join within the function.
                Defaults to True.
        """
        self._kill = True
        if wait is True and self._watcher_thread.is_alive():
            self._watcher_thread.join()
        self._has_started = False

    def reset(self) -> None:
        """Stops the running threads and reset the instance to its initial state"""
        self.stop()
        self._setup()

    def add_event_callback(
        self,
        event: ContractEvent,
        callback: Callable[[AttributeDict], None],
        delay: float = 2.0,
        repeat: bool = True,
    ) -> None:
        """
        Adds a callback instruction for the specified event.

        Args:
            event (ContractEvent): The ContractEvent instance to watch for.
            callback (Callable[[AttributeDict], None]): The function to be called
                when a new 'event' is detected.
            delay (float, optional): The delay between each check for new 'event'(s).
                Defaults to 2.0.
            repeat (bool, optional): Whether to repeat the callback or not (if False,
                the callback will be called once only). Defaults to True.

        Raises:
            TypeError: Raises when the parameter 'callback' is not a callable object.
        """
        if not callable(callback):
            raise TypeError("Argument 'callback' argument must be a callable.")
        delay = max(delay, 0.05)
        self.target_list_lock.acquire()  # lock
        # Key referring to this specific event (event.address is the address
        # of the contract to which the event is linked)
        event_watch_data_key = f"{str(event.address)}+{event.event_name}"
        if self.target_events_watch_data.get(event_watch_data_key) is None:
            # If the _EventWatchData for 'event' does not exist, creates it.
            self.target_events_watch_data[event_watch_data_key] = _EventWatchData(
                event, callback, delay, repeat
            )
        else:
            # Adds a new callback to the already existing _EventWatchData.
            self.target_events_watch_data[event_watch_data_key].add_callback(callback, repeat)
            if repeat is True:
                # Updates the delay between each check calling the
                # _EventWatchData.update_delay function
                self.target_events_watch_data[event_watch_data_key].update_delay(delay)
        self.target_list_lock.release()  # unlock
        # Start watch if not done
        if self._has_started is False:
            self._start_watch()

    def _setup(self) -> None:
        """Sets up the EventWatcher instance member variables so it is ready to run"""
        self.target_list_lock.acquire()
        self.target_events_watch_data.clear()
        self.target_list_lock.release()
        self._kill = False
        self._has_started = False
        self._watcher_thread = Thread(target=self._loop, daemon=True)

    def _start_watch(self) -> None:
        """Starts the thread running the _loop function"""
        self._watcher_thread.start()
        self._has_started = True

    def _loop(self) -> None:
        """
        Watches for new events. Whenever new events are detected, calls the
        '_EventWatchData._trigger_callbacks' function to run the callbacks instructions
        (in separate threads) on the detected events data.
        """
        workers_list: list[Thread] = []

        while not self._kill:
            try:
                sleep_time: float = 1.0  # Max sleep time.
                self.target_list_lock.acquire()  # lock
                for _, elem in self.target_events_watch_data.items():
                    # If cooldown is not over :
                    #   skip and store time left before next check if needed.
                    time_left = elem.time_left
                    if time_left > 0:
                        sleep_time = min(sleep_time, time_left)
                        continue
                    # Check for new events & execute callback async if some are found
                    latest_events = elem.get_new_events()
                    if len(latest_events) != 0:
                        workers_list += elem._trigger_callbacks(latest_events)
                    elem.reset_timer()
                    # after elem.reset_timer elem.time_left is approximately elem.delay
                    sleep_time = min(sleep_time, elem.time_left)
            finally:
                self.target_list_lock.release()  # unlock
                # Remove dead threads from the workers_list
                workers_list = list(filter(lambda x: x.is_alive(), workers_list))
                time.sleep(sleep_time)

        # Join running threads when leaving function.
        for worker_instance in workers_list:
            worker_instance.join(timeout=30)
            if worker_instance.is_alive():
                worker_name = worker_instance.getName()
                warnings.warn(
                    message=f"Callback execution ({worker_name}) could not be joined.",
                    category=RuntimeWarning,
                )


def __get_path() -> Path:
    return _get_data_folder().joinpath("topics.json")


def _get_topics(abi: list[ABIElement]) -> dict[str, HexStr]:
    topic_map = eth_event.get_topic_map(abi)

    updated_topics = _topics.copy()

    for key, value in topic_map.items():
        if key not in updated_topics:
            # new event topic
            updated_topics[key] = value
        elif value == updated_topics[key]:
            # existing event topic, nothing has changed
            continue
        elif not any(i["indexed"] for i in updated_topics[key]["inputs"]):
            # existing topic, but the old abi has no indexed events - keep the new one
            updated_topics[key] = value

    if updated_topics != _topics:
        _topics.update(updated_topics)
        with __get_path().open("w") as fp:
            ujson_dump(updated_topics, fp, sort_keys=True, indent=2)

    return {v["name"]: k for k, v in topic_map.items()}


def _add_deployment_topics(address: ChecksumAddress, abi: list[ABIElement]) -> None:
    _deployment_topics[address] = eth_event.get_topic_map(abi)


def _decode_logs(
    # Mapping is included so we don't break dependent lib ypricemagic with this change
    logs: list[_EventItem] | list[Mapping[str, Any]],
    contracts: dict[ChecksumAddress, "Contract"] | None = None,
) -> EventDict:
    if not logs:
        return EventDict()

    idx = 0
    events: list[DecodedEvent | NonDecodedEvent] = []
    while True:
        address: ChecksumAddress = logs[idx]["address"]
        try:
            new_idx = logs.index(
                next(i for i in logs[idx:] if i["address"] != address)  # type: ignore [misc]
            )
            log_slice = logs[idx:new_idx]
            idx = new_idx
        except StopIteration:
            log_slice = logs[idx:]

        topics_map = _deployment_topics.get(address, _topics)
        for item in log_slice:
            if contracts:
                contract = contracts[address]
                if contract is not None:
                    note = _decode_ds_note(item, contract)
                    if note is not None:
                        events.append(note)
                        continue
            try:
                events.extend(
                    eth_event.decode_logs([item], topics_map, allow_undecoded=True)  # type: ignore [call-overload]
                )
            except EventError as exc:
                warnings.warn(f"{address}: {exc}")

        if log_slice[-1] == logs[-1]:
            break

    return EventDict(format_event(event) for event in events)


def _decode_ds_note(
    log: _EventItem | Mapping[str, Any], contract: "Contract"
) -> DecodedEvent | None:
    # ds-note encodes function selector as the first topic
    # TODO double check typing for `log` input
    topic0 = log.topics[0]
    selector, tail = topic0[:4], topic0[4:]
    selector_hexstr = Selector(hexbytes_to_hexstring(selector))
    if selector_hexstr not in contract.selectors or sum(tail):
        return None
    name = contract.selectors[selector_hexstr]
    log_data = log.data
    data = bytes.fromhex(log_data[2:]) if isinstance(log_data, str) else log_data
    # data uses ABI encoding of [uint256, bytes] or [bytes] in different versions
    # instead of trying them all, assume the payload starts from selector
    try:
        func, args = contract.decode_input(data[data.index(selector) :])
    except ValueError:
        return None
    selector_hexstr = Selector(hexbytes_to_hexstring(selector))
    inputs = contract.get_method_object(selector_hexstr).abi["inputs"]
    return DecodedEvent(
        name=name,
        address=cast(ChecksumAddress, log.address),
        decoded=True,
        data=[
            {"name": abi["name"], "type": abi["type"], "value": arg, "decoded": True}
            for arg, abi in zip(args, inputs)
        ],
    )


def _decode_trace(trace: Sequence[_TraceStep], initial_address: AnyAddress) -> EventDict:
    if not trace:
        return EventDict()

    events = eth_event.decode_traceTransaction(
        trace if type(trace) is list else list(trace),
        _topics,
        allow_undecoded=True,
        initial_address=initial_address,
    )
    return EventDict(format_event(event) for event in events)


# dictionary of event topic ABIs specific to a single contract deployment
_deployment_topics: Final[DeploymentTopics] = {}

# EventWatcher program instance
event_watcher: Final = EventWatcher()

try:
    with __get_path().open() as fp:
        __topics = ujson_load(fp)
except (FileNotFoundError, JSONDecodeError):
    __topics = None

# general event topic ABIs for decoding events on unknown contracts
_topics: Final[TopicMap] = __topics or {}
del __topics
