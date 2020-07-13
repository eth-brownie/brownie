#!/usr/bin/python3

import pytest

from brownie import compile_source
from brownie.exceptions import EventLookupError
from brownie.network.event import EventDict, _EventItem


@pytest.fixture
def event(accounts, tester):
    tx = tester.emitEvents("foo bar", 42)
    return tx.events


def test_tuple_values(accounts, tester):
    value = ["blahblah", accounts[1], ("yesyesyes", "0x1234")]
    tx = tester.setTuple(value)
    assert tx.events[0]["addr"] == accounts[1]
    assert tx.events[0]["base"] == value


def test_types(event):
    assert type(event) is EventDict
    assert type(event[0]) is _EventItem
    assert type(event["Debug"]) is _EventItem
    assert type(event["IndexedEvent"]) is _EventItem


def test_address(event, tester):
    assert event["Debug"].address is None
    assert event["Debug"][0].address == tester


def test_count(event):
    assert len(event) == 3
    assert event.count("IndexedEvent") == len(event["IndexedEvent"]) == 1
    assert event.count("Debug") == len(event["Debug"]) == 2


def test_equality(event):
    assert event[1] == event["IndexedEvent"]
    assert event[0] != event["Debug"]
    assert event[0] == event["Debug"][0]
    assert event[0] != event[-1]


def test_pos(event):
    assert event[0].pos == (0,)
    assert event["Debug"].pos == (0, 2)
    assert event["IndexedEvent"].pos == (1,)


def test_contains(event):
    assert "Debug" in event
    assert "Debug" not in event["Debug"]
    assert "a" not in event
    assert "a" in event["Debug"]


def test_keys(event):
    assert event.keys() == ["Debug", "IndexedEvent"]
    assert event["IndexedEvent"].keys() == ["str", "num"]


def test_str(event):
    str(event)
    str(event["Debug"])
    str(event["IndexedEvent"])


def test_indexed(event):
    assert event["IndexedEvent"]["str"] == event["IndexedEvent"]["str (indexed)"]
    assert str(event["IndexedEvent"]["str"]) != "foo bar"
    assert event["IndexedEvent"]["num"] == 42


def test_eventdict_raises(event):
    with pytest.raises(TypeError):
        event[23.3]
    with pytest.raises(EventLookupError):
        event[4]
    with pytest.raises(EventLookupError):
        event["foo"]


def test_eventitem_raises(event):
    with pytest.raises(TypeError):
        event["Debug"][23.3]
    with pytest.raises(EventLookupError):
        event["Debug"][4]
    with pytest.raises(EventLookupError):
        event["Debug"]["foo"]


def test_same_topic_different_abi(accounts):
    proj = compile_source(
        """
    pragma solidity 0.5.0;

    contract Foo {
        event Baz(uint256 indexed a, uint256 b, uint256 c);
        function foo() public {
            emit Baz(1, 2, 3);
        }
    }

    contract Bar {
        event Baz(uint256 indexed a, uint256 b, uint256 indexed c);
        function bar(Foo _addr) public {
            _addr.foo();
            emit Baz(4, 5, 6);
        }
    }"""
    )

    foo = proj.Foo.deploy({"from": accounts[0]})
    bar = proj.Bar.deploy({"from": accounts[0]})
    tx = bar.bar(foo, {"from": accounts[0]})
    assert len(tx.events) == 2
    assert tx.events[0].values() == [1, 2, 3]
    assert tx.events[1].values() == [4, 5, 6]
