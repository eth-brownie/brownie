#!/usr/bin/python3

import json
from pathlib import Path

import eth_event

from brownie.convert import format_event
from brownie._config import CONFIG


class EventDict:
    '''Dict/list hybrid container, base class for all events fired in a transaction.'''

    def __init__(self, events):
        '''Instantiates the class.

        Args:
            events: event data as supplied by eth_event.decode_logs or eth_event.decode_trace'''
        self._ordered = [_EventItem(
            i['name'],
            [dict((x['name'], x['value']) for x in i['data'])],
            (pos,)
        ) for pos, i in enumerate(events)]
        self._dict = {}
        for event in self._ordered:
            if event.name in self._dict:
                continue
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
        if type(key) is int:
            return self._ordered[key]
        return self._dict[key]

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
        '''EventDict.items() -> a set-like object providing a view on EventDict's items'''
        return self._dict.items()

    def keys(self):
        '''EventDict.keys() -> a set-like object providing a view on EventDict's keys'''
        return self._dict.keys()

    def values(self):
        '''EventDict.values() -> an object providing a view on EventDict's values'''
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
        if type(key) is int:
            return self._ordered[key]
        return self._ordered[0][key]

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
        return other == self._ordered

    def items(self):
        '''_EventItem.items() -> a set-like object providing a view on _EventItem[0]'s items'''
        return self._ordered[0].items()

    def keys(self):
        '''_EventItem.keys() -> a set-like object providing a view on _EventItem[0]'s keys'''
        return self._ordered[0].keys()

    def values(self):
        '''_EventItem.values() -> an object providing a view on _EventItem[0]'s values'''
        return self._ordered[0].values()


def _get_path():
    return Path(CONFIG['folders']['brownie']).joinpath('data/topics.json')


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
