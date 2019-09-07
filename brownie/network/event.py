#!/usr/bin/python3

from collections import OrderedDict
import json

import eth_event

from brownie.convert import format_event
from brownie._config import CONFIG
from brownie.exceptions import EventLookupError


class EventDict:
    '''Dict/list hybrid container, base class for all events fired in a transaction.'''

    def __init__(self, events):
        '''Instantiates the class.

        Args:
            events: event data as supplied by eth_event.decode_logs or eth_event.decode_trace'''
        self._ordered = [_EventItem(
            i['name'],
            [OrderedDict((x['name'], x['value']) for x in i['data'])],
            (pos,)
        ) for pos, i in enumerate(events)]
        self._dict = OrderedDict()
        for event in self._ordered:
            if event.name not in self._dict:
                events = [i for i in self._ordered if i.name == event.name]
                self._dict[event.name] = _EventItem(
                    event.name,
                    events,
                    tuple(i.pos[0] for i in events)
                )

    def __repr__(self):
        return str(self)

    def __bool__(self):
        return bool(self._ordered)

    def __contains__(self, name):
        '''returns True if an event fired with the given name.'''
        return name in [i.name for i in self._ordered]

    def __getitem__(self, key):
        '''if key is int: returns the n'th event that was fired
        if key is str: returns a _EventItem dict of all events where name == key'''
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

    def __iter__(self):
        return iter(self._ordered)

    def __len__(self):
        '''returns the number of events that fired.'''
        return len(self._ordered)

    def __str__(self):
        return str(dict((k, [i[0] for i in v._ordered]) for k, v in self._dict.items()))

    def count(self, name):
        '''EventDict.count(name) -> integer -- return number of occurrences of name'''
        return len([i.name for i in self._ordered if i.name == name])

    def items(self):
        '''EventDict.items() -> a list object providing a view on EventDict's items'''
        return list(self._dict.items())

    def keys(self):
        '''EventDict.keys() -> a list object providing a view on EventDict's keys'''
        return list(self._dict.keys())

    def values(self):
        '''EventDict.values() -> a list object providing a view on EventDict's values'''
        return self._dict.values()


class _EventItem:
    '''Dict/list hybrid container, represents one or more events with the same name
    that were fired in a transaction.

    Attributes:
        name: event name
        pos: tuple of indexes where this event fired'''

    def __init__(self, name, event_data, pos):
        self.name = name
        self._ordered = event_data
        self.pos = pos

    def __getitem__(self, key):
        '''if key is int: returns the n'th event that was fired with this name
        if key is str: returns the value of data field 'key' from the 1st event
        within the container '''
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

    def __contains__(self, name):
        '''returns True if this event contains a value with the given name.'''
        return name in self._ordered[0]

    def __len__(self):
        '''returns the number of events held in this container.'''
        return len(self._ordered)

    def __repr__(self):
        return str(self)

    def __str__(self):
        if len(self._ordered) == 1:
            return str(self._ordered[0])
        return str([i[0] for i in self._ordered])

    def __iter__(self):
        return iter(self._ordered)

    def __eq__(self, other):
        if len(self._ordered) == 1:
            return other == self._ordered[0]
        return other == self._ordered

    def items(self):
        '''_EventItem.items() -> a list object providing a view on _EventItem[0]'s items'''
        return [(i, self[i]) for i in self.keys()]

    def keys(self):
        '''_EventItem.keys() -> a list object providing a view on _EventItem[0]'s keys'''
        return [i.replace(" (indexed)", "") for i in self._ordered[0].keys()]

    def values(self):
        '''_EventItem.values() -> a list object providing a view on _EventItem[0]'s values'''
        return list(self._ordered[0].values())


def _get_path():
    return CONFIG['brownie_folder'].joinpath('data/topics.json')


def get_topics(abi):
    new_topics = _topics.copy()
    new_topics.update(eth_event.get_event_abi(abi))
    if new_topics != _topics:
        _topics.update(new_topics)
        with _get_path().open('w') as fp:
            json.dump(new_topics, fp, sort_keys=True, indent=2)
    return eth_event.get_topics(abi)


def decode_logs(logs):
    if not logs:
        return []
    events = eth_event.decode_logs(logs, _topics)
    events = [format_event(i) for i in events]
    return EventDict(events)


def decode_trace(trace):
    if not trace:
        return []
    events = eth_event.decode_trace(trace, _topics)
    events = [format_event(i) for i in events]
    return EventDict(events)


try:
    with _get_path().open() as fp:
        _topics = json.load(fp)
except (FileNotFoundError, json.decoder.JSONDecodeError):
    _topics = {}
