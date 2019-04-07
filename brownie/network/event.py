#!/usr/bin/python3

import json
from pathlib import Path

import eth_event

import brownie.config as config
CONFIG = config.CONFIG


def get_topics(abi):
    new_topics = _topics.copy()
    new_topics.update(eth_event.get_event_abi(abi))
    if new_topics != _topics:
        _topics.update(new_topics)
        json.dump(  
            new_topics,
            Path(CONFIG['folders']['brownie']).joinpath('topics.json').open('w'),
            sort_keys=True,
            indent=4
        )
    return eth_event.get_topics(abi)


def decode_logs(logs):
    try:
        eth_event.decode_logs(logs, _topics)
    except Exception:
        return []


def decode_trace(trace):
    try:
        eth_event.decode_trace(trace, _topics)
    except Exception:
        return []


try:
    _topics = json.load(Path(CONFIG['folders']['brownie']).joinpath('topics.json').open())
except (FileNotFoundError, json.decoder.JSONDecodeError):
    _topics = {}
