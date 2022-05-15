#!/usr/bin/python3

import asyncio
import time

import pytest
from web3.datastructures import AttributeDict
from web3.exceptions import ABIEventFunctionNotFound

from brownie import Contract, compile_source
from brownie.exceptions import EventLookupError
from brownie.network.event import EventDict, EventWatcher, _EventItem, event_watcher
from brownie.network.transaction import TransactionReceipt


@pytest.fixture
def event(accounts, tester):
    tx = tester.emitEvents("foo bar", 42)
    return tx.events


@pytest.fixture
def event_watcher_instance():
    return event_watcher


def wait_for_tx(tx: TransactionReceipt, n: int = 1):
    if tx.confirmations != n:
        tx.wait(n)


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


# Blocks 0 and 1 are automatically skipped
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


class TestEventWatcher:
    """
    Class testing the event subscription feature using the
    brownie.network.event.event_watcher global variable
    which is multi-threaded and needs to be reset between each test.
    """

    @pytest.fixture(scope="function", autouse=True)
    def event_watcher_reset(self, event_watcher_instance: EventWatcher):
        """Resets the event_watcher instance between each test in the class"""
        event_watcher_instance.reset()

    def test_can_subscribe_to_event_with_callback(_, tester: Contract):
        expected_num: int = round(time.time()) % 100  # between 0 and 99
        received_num: int = -1
        callback_was_triggered: bool = False

        def _callback(data):
            nonlocal received_num, callback_was_triggered
            received_num = data["args"]["num"]
            callback_was_triggered = True

        tester.events.subscribe("IndexedEvent", callback=_callback, delay=0.05)
        wait_for_tx(tester.emitEvents("", expected_num))
        time.sleep(0.1)

        assert callback_was_triggered is True, "Callback was not triggered."
        assert expected_num == received_num, "Callback was not triggered with the right event"

    def test_can_subscribe_to_event_with_multiple_callbacks(_, tester: Contract):
        callback_trigger_1: bool = False
        callback_trigger_2: bool = False

        def _cb1(_):
            nonlocal callback_trigger_1
            callback_trigger_1 = True

        def _cb2(_):
            nonlocal callback_trigger_2
            callback_trigger_2 = True

        tester.events.subscribe("IndexedEvent", callback=_cb1, delay=0.05)
        tester.events.subscribe("IndexedEvent", callback=_cb2, delay=0.05)
        wait_for_tx(tester.emitEvents("", 0))
        time.sleep(0.1)

        assert callback_trigger_1 is True, "Callback 1 was not triggered"
        assert callback_trigger_2 is True, "Callback 2 was not triggered"

    def test_callback_can_be_triggered_multiple_times(_, tester: Contract):
        callback_trigger_count = 0
        expected_callback_trigger_count = 2

        def _cb(_):
            nonlocal callback_trigger_count
            callback_trigger_count += 1

        tester.events.subscribe("Debug", callback=_cb, delay=0.05)
        wait_for_tx(tester.emitEvents("", 0))
        time.sleep(0.1)

        assert (
            callback_trigger_count == expected_callback_trigger_count
        ), "Callback was not triggered the exact number of time it should have"

    def test_event_listener_can_timeout(_, tester: Contract):
        task = tester.events.listen("IndexedEvent", timeout=1.0)

        # Using asyncio.wait_for to avoid infinite loop.
        result = asyncio.run(asyncio.wait_for(task, timeout=1.2))

        assert result["event_data"] is None, "Listener was triggered during test."
        assert result["timed_out"] is True, "Listener did not timed out."

    def test_can_listen_for_event(_, tester: Contract):
        expected_num = round(time.time()) % 100  # between 0 and 99
        listener = tester.events.listen("IndexedEvent", timeout=10.0)

        wait_for_tx(tester.emitEvents("", expected_num))

        result: AttributeDict = asyncio.run(listener)

        assert result.get("timed_out") is False, "Event listener timed out."
        assert expected_num == result.event_data["args"]["num"]

    def test_not_repeating_callback_is_removed_after_triggered(_, tester: Contract):
        expected_trigger_count: int = 1
        trigger_count: int = 0

        def _cb(_):
            nonlocal trigger_count
            trigger_count += 1

        event_watcher.add_event_callback(
            event=tester.events.IndexedEvent, callback=_cb, delay=0.05, repeat=False
        )

        wait_for_tx(tester.emitEvents("", 0))
        time.sleep(0.1)
        wait_for_tx(tester.emitEvents("", 0))
        time.sleep(0.1)

        assert trigger_count == expected_trigger_count

    def test_can_set_both_repeating_and_not_repeating_callback_on_the_same_event(
        _, tester: Contract
    ):
        expected_trigger_count: int = 3
        trigger_count: int = 0

        def _cb(_):
            nonlocal trigger_count
            trigger_count += 1

        event_watcher.add_event_callback(
            event=tester.events.IndexedEvent, callback=_cb, delay=0.05, repeat=False
        )
        event_watcher.add_event_callback(
            event=tester.events.IndexedEvent, callback=_cb, delay=0.05, repeat=True
        )

        wait_for_tx(tester.emitEvents("", 0))
        time.sleep(0.1)
        wait_for_tx(tester.emitEvents("", 0))
        time.sleep(0.1)

        assert trigger_count == expected_trigger_count

    @pytest.mark.skip(reason="For developping purpose")
    def test_scripting(_, tester: Contract):
        pass
