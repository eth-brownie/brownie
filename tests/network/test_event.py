#!/usr/bin/python3

import pytest

from brownie.network.event import EventDict, _EventItem


@pytest.fixture
def event(accounts, tester):
    value = ["blahblah", accounts[1], ("yesyesyes", "0x1234")]
    tx = tester.setTuple(value)
    return tx.events


def test_values(accounts, event):
    assert event[0]['addr'] == accounts[1]
    assert event[0]['base'] == ["blahblah", accounts[1], ("yesyesyes", "0x1234")]


def test_types(event):
    assert type(event) is EventDict
    assert type(event[0]) is _EventItem
    assert type(event['TupleEvent']) is _EventItem


def test_count(event):
    assert len(event) == 1
    assert event.count('TupleEvent') == 1


def test_equality_getitem_pos(event):
    assert event[0] == event['TupleEvent']
    assert event[0].pos == (0,)


def test_str(event):
    str(event)
    str(event[0])
    str(event['TupleEvent'])
