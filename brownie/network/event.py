#!/usr/bin/python3

import json
from pathlib import Path

import eth_event

from brownie.types import EventDict
from brownie.types.convert import format_event
from brownie._config import CONFIG


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
