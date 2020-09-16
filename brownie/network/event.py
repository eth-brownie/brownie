#!/usr/bin/python3

import json
import warnings
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple, Union, ValuesView

import eth_event
from eth_event import EventError

from brownie._config import _get_data_folder
from brownie.convert.normalize import format_event
from brownie.exceptions import EventLookupError


class EventDict:
    """
    Dict/list hybrid container, base class for all events fired in a transaction.
    """

    def __init__(self, events: List) -> None:
        """Instantiates the class.

        Args:
            events: event data as supplied by eth_event.decode_logs or eth_event.decode_trace"""
        self._ordered = [
            _EventItem(
                i["name"],
                i["address"],
                [OrderedDict((x["name"], x["value"]) for x in i["data"])],
                (pos,),
            )
            for pos, i in enumerate(events)
        ]

        self._dict: Dict = OrderedDict()
        for event in self._ordered:
            if event.name not in self._dict:
                events = [i for i in self._ordered if i.name == event.name]
                self._dict[event.name] = _EventItem(
                    event.name, None, events, tuple(i.pos[0] for i in events)
                )

    def __repr__(self) -> str:
        return str(self)

    def __bool__(self) -> bool:
        return bool(self._ordered)

    def __contains__(self, name: str) -> bool:
        """returns True if an event fired with the given name."""
        return name in [i.name for i in self._ordered]

    def __getitem__(self, key: Union[str, int]) -> "_EventItem":
        """if key is int: returns the n'th event that was fired
        if key is str: returns a _EventItem dict of all events where name == key"""
        if not isinstance(key, (int, str)):
            raise TypeError(f"Invalid key type '{type(key)}' - can only use strings or integers")
        if isinstance(key, int):
            try:
                return self._ordered[key]
            except IndexError:
                raise EventLookupError(
                    f"Index out of range - only {len(self._ordered)} events fired"
                )
        if key in self._dict:
            return self._dict[key]
        raise EventLookupError(f"Event '{key}' did not fire.")

    def __iter__(self) -> Iterator:
        return iter(self._ordered)

    def __len__(self) -> int:
        """returns the number of events that fired."""
        return len(self._ordered)

    def __str__(self) -> str:
        return str(dict((k, [i[0] for i in v._ordered]) for k, v in self._dict.items()))

    def count(self, name: str) -> int:
        """EventDict.count(name) -> integer -- return number of occurrences of name"""
        return len([i.name for i in self._ordered if i.name == name])

    def items(self) -> List:
        """EventDict.items() -> a list object providing a view on EventDict's items"""
        return list(self._dict.items())

    def keys(self) -> List:
        """EventDict.keys() -> a list object providing a view on EventDict's keys"""
        return list(self._dict.keys())

    def values(self) -> ValuesView:
        """EventDict.values() -> a list object providing a view on EventDict's values"""
        return self._dict.values()


class _EventItem:
    """
    Dict/list hybrid container, represents one or more events with the same name
    that were fired in a transaction.

    Attributes
    ----------
    name : str
        Name of the event.
    address : str
        Address where this event fired. When the object represents more than one event,
        this value is set to `None`.
    pos : tuple
        Tuple of indexes where this event fired.
    """

    def __init__(self, name: str, address: Optional[str], event_data: List, pos: Tuple) -> None:
        self.name = name
        self.address = address
        self._ordered = event_data
        self.pos = pos

    def __getitem__(self, key: Union[int, str]) -> List:
        """if key is int: returns the n'th event that was fired with this name
        if key is str: returns the value of data field 'key' from the 1st event
        within the container """
        if not isinstance(key, (int, str)):
            raise TypeError(f"Invalid key type '{type(key)}' - can only use strings or integers")
        if isinstance(key, int):
            try:
                return self._ordered[key]
            except IndexError:
                raise EventLookupError(
                    f"Index out of range - only {len(self._ordered)} '{self.name}' events fired"
                )
        if key in self._ordered[0]:
            return self._ordered[0][key]
        if f"{key} (indexed)" in self._ordered[0]:
            return self._ordered[0][f"{key} (indexed)"]
        valid_keys = ", ".join(self.keys())
        raise EventLookupError(
            f"Unknown key '{key}' - the '{self.name}' event includes these keys: {valid_keys}"
        )

    def __contains__(self, name: str) -> bool:
        """returns True if this event contains a value with the given name."""
        return name in self._ordered[0]

    def __len__(self) -> int:
        """returns the number of events held in this container."""
        return len(self._ordered)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        if len(self._ordered) == 1:
            return str(self._ordered[0])
        return str([i[0] for i in self._ordered])

    def __iter__(self) -> Iterator:
        return iter(self._ordered)

    def __eq__(self, other: object) -> bool:
        if len(self._ordered) == 1:
            return other == self._ordered[0]
        return other == self._ordered

    def items(self) -> List:
        """_EventItem.items() -> a list object providing a view on _EventItem[0]'s items"""
        return [(i, self[i]) for i in self.keys()]

    def keys(self) -> List:
        """_EventItem.keys() -> a list object providing a view on _EventItem[0]'s keys"""
        return [i.replace(" (indexed)", "") for i in self._ordered[0].keys()]

    def values(self) -> List:
        """_EventItem.values() -> a list object providing a view on _EventItem[0]'s values"""
        return list(self._ordered[0].values())


def __get_path() -> Path:
    return _get_data_folder().joinpath("topics.json")


def _get_topics(abi: List) -> Dict:
    topic_map = eth_event.get_topic_map(abi)

    updated_topics = _topics.copy()

    for key, value in topic_map.items():
        if key not in updated_topics:
            # new event topic
            updated_topics[key] = value
        elif value == updated_topics[key]:
            # existing event topic, nothing has changed
            continue
        elif not next((i for i in updated_topics[key]["inputs"] if i["indexed"]), False):
            # existing topic, but the old abi has no indexed events - keep the new one
            updated_topics[key] = value

    if updated_topics != _topics:
        _topics.update(updated_topics)
        with __get_path().open("w") as fp:
            json.dump(updated_topics, fp, sort_keys=True, indent=2)

    return {v["name"]: k for k, v in topic_map.items()}


def _add_deployment_topics(address: str, abi: List) -> None:
    _deployment_topics[address] = eth_event.get_topic_map(abi)


def _decode_logs(logs: List) -> Union["EventDict", List[None]]:
    if not logs:
        return []

    idx = 0
    events: List = []
    while True:
        address = logs[idx]["address"]
        try:
            new_idx = logs.index(next(i for i in logs[idx:] if i["address"] != address))
            log_slice = logs[idx:new_idx]
            idx = new_idx
        except StopIteration:
            log_slice = logs[idx:]

        topics_map = _deployment_topics.get(address, _topics)
        for item in log_slice:
            try:
                events.extend(eth_event.decode_logs([item], topics_map, allow_undecoded=True))
            except EventError as exc:
                warnings.warn(str(exc))

        if log_slice[-1] == logs[-1]:
            break

    events = [format_event(i) for i in events]
    return EventDict(events)


def _decode_trace(trace: Sequence, initial_address: str) -> Union["EventDict", List[None]]:
    if not trace:
        return []

    events = eth_event.decode_traceTransaction(
        trace, _topics, allow_undecoded=True, initial_address=initial_address
    )
    events = [format_event(i) for i in events]
    return EventDict(events)


# dictionary of event topic ABIs specific to a single contract deployment
_deployment_topics: Dict = {}

# general event topic ABIs for decoding events on unknown contracts
_topics: Dict = {}

try:
    with __get_path().open() as fp:
        _topics = json.load(fp)
except (FileNotFoundError, json.decoder.JSONDecodeError):
    pass
