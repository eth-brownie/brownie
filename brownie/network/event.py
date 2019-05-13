#!/usr/bin/python3

import json
from pathlib import Path

import eth_event

from brownie.types import EventDict
from brownie._config import CONFIG


def _get_path():
    return Path(CONFIG['folders']['brownie']).joinpath('data/topics.json')


def get_topics(abi):
    new_topics = _topics.copy()
    new_topics.update(eth_event.get_event_abi(abi))
    if new_topics != _topics:
        _topics.update(new_topics)
        json.dump(
            new_topics,
            _get_path().open('w'),
            sort_keys=True,
            indent=2
        )
    return eth_event.get_topics(abi)


def decode_logs(logs):
    try:
        return EventDict(eth_event.decode_logs(logs, _topics))
    except Exception:
        return []


def decode_trace(trace):
    try:
        return EventDict(eth_event.decode_trace(trace, _topics))
    except Exception:
        return []


try:
    _topics = json.load(_get_path().open())
except (FileNotFoundError, json.decoder.JSONDecodeError):
    _topics = {}
