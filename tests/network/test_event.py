#!/usr/bin/python3

import pytest

from brownie import accounts
from brownie.network.event import EventDict, _EventItem


@pytest.fixture(scope="module")
def txevents(token):
    tx = token.transfer(accounts[1], 100, {'from': accounts[0]})
    yield tx.events


def test_tuples(tupletester):
    value = ["blahblah", accounts[1], ("yesyesyes", "0x1234")]
    tx = tupletester.setTuple(value)
    assert tx.events[0]['base'] == value


def test_types(txevents):
    assert type(txevents) is EventDict
    assert type(txevents[0]) is _EventItem
    assert type(txevents['Transfer']) is _EventItem


def test_count(txevents):
    assert len(txevents) == 1
    assert txevents.count('Transfer') == 1


def test_equality_getitem_pos(txevents):
    assert txevents[0] == txevents['Transfer']
    assert txevents[0].pos == (0,)


def test_str(txevents):
    str(txevents)
    str(txevents[0])
    str(txevents['Transfer'])
