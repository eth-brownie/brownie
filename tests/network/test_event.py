#!/usr/bin/python3

import time

import pytest
from web3.datastructures import AttributeDict
from web3.exceptions import ABIEventFunctionNotFound

from brownie import Contract, compile_source
from brownie.exceptions import EventLookupError
from brownie.network.alert import event_watcher
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


def test_can_retrieve_contract_events_on_previously_mined_blocks(tester: Contract):
    number_of_events_to_fire = 15
    from_block = 4
    to_block = 12

    # Emit events & mined blocks
    for i in range(number_of_events_to_fire):
        tx = tester.emitEvents("Just testing events", i)
        if tx.confirmations == 0:
            tx.wait(1)
    # Get all contract events between specified blocks
    result = tester.events.get_sequence(from_block=from_block, to_block=to_block)

    # Assert
    assert isinstance(result, AttributeDict)
    assert all(
        [
            (
                result["Debug"][i * 2]["blockNumber"] == from_block + i  # noqa
                and result["Debug"][i * 2 + 1]["blockNumber"] == from_block + i
            )
            for i in range(to_block - from_block)
        ]
    )
    assert all(
        [
            (result["IndexedEvent"][i]["blockNumber"] == from_block + i)
            for i in range(to_block - from_block)
        ]
    )


# Why are blocks 0 & 1 automatically skipped :(
def test_can_retrieve_specified_events_on_previously_mined_blocks(tester: Contract):
    number_of_events_to_fire = 15
    event_name = "IndexedEvent"
    from_block = 2
    to_block = 10

    # Emit events & mined blocks
    for i in range(number_of_events_to_fire):
        tx = tester.emitEvents("Just testing events", i)
        if tx.confirmations == 0:
            tx.wait(1)
    # Get events of type between
    result = tester.events.get_sequence(
        from_block=from_block, to_block=to_block, event_type=event_name
    )

    # Assert
    for i in range(from_block, to_block - 1):
        assert result[i]["args"]["num"] == i


def test_cannot_subscribe_to_unexisting_event(tester: Contract):
    with pytest.raises(ABIEventFunctionNotFound):
        tester.events.subscribe("InvalidEventName", callback=(lambda x: x))


def test_cannot_subscribe_to_event_with_invalid_callback(tester: Contract):
    with pytest.raises(TypeError):
        tester.events.subscribe("Debug", callback=None)  # type: ignore


@pytest.mark.skip(reason="Test not fully programmed")
def test_can_subscribe_to_event(tester: Contract):
    print("[MAIN] - Starting...")

    def _callback(data):
        print("[CALLBACK] - Event received with value {}".format(data["args"]["num"]))

    tester.events.subscribe("IndexedEvent", callback=_callback)
    for i in range(25):
        tester.emitEvents("", i)
        time.sleep(5)
    print("[MAIN] - Stopping...")
    event_watcher.stop()
    print("[MAIN] - Done !")
