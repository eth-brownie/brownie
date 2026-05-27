#!/usr/bin/python3

import asyncio
import time
from threading import Event as ThreadEvent
from threading import Lock, Thread

import pytest
from web3.datastructures import AttributeDict
from web3.exceptions import ABIEventNotFound

from brownie import Contract, compile_source
from brownie.exceptions import EventLookupError
from brownie.network.event import (
    EventDict,
    EventWatcher,
    _create_event_filter,
    _EventItem,
    _is_provider_teardown_error,
    event_watcher,
)
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


def wait_for_no_callback(callback_event: ThreadEvent, timeout: float = 0.2) -> None:
    assert callback_event.wait(timeout) is False


class _BlockingEventWatchData:
    delay = 0.05

    def __init__(self, events=None):
        self.events = events or []
        self.callbacks = [{"function": lambda _: None, "repeat": True}]
        self.poll_started = ThreadEvent()
        self.release_poll = ThreadEvent()
        self.callback_triggered = ThreadEvent()
        self.timer = time.time() - self.delay

    @property
    def time_left(self):
        return 0.0

    def get_new_events(self):
        self.poll_started.set()
        self.release_poll.wait(1.0)
        return self.events

    def reset_timer(self):
        self.timer = time.time()

    def add_callback(self, callback, repeat=True):
        self.callbacks.append({"function": callback, "repeat": repeat})

    def update_delay(self, new_delay):
        self.delay = min(self.delay, new_delay)

    def _trigger_callbacks(self, _):
        self.callback_triggered.set()
        return []


class _FakeEvent:
    address = "0x0000000000000000000000000000000000000000"
    event_name = "FakeEvent"


class _FilterRecorder:
    def __init__(self):
        self.calls = []

    def create_filter(self, **kwargs):
        self.calls.append(kwargs)
        return "filter"


def fake_event_key(event):
    return f"{str(event.address)}+{event.event_name}"


def start_watcher_with_target(event_watcher_instance, watch_data):
    with event_watcher_instance.target_list_lock:
        event_watcher_instance.target_events_watch_data[fake_event_key(_FakeEvent)] = watch_data
    event_watcher_instance._start_watch()
    assert watch_data.poll_started.wait(1.0) is True
    return event_watcher_instance._watcher_thread


def release_and_join_watcher(watch_data, watcher_thread):
    watch_data.release_poll.set()
    watcher_thread.join(timeout=1.0)


def test_create_event_filter_uses_web3_v7_keywords():
    event = _FilterRecorder()

    event_filter = _create_event_filter(event, from_block=4, to_block=12)

    assert event_filter == "filter"
    assert event.calls == [{"from_block": 4, "to_block": 12}]


def test_create_event_filter_omits_missing_to_block():
    event = _FilterRecorder()

    event_filter = _create_event_filter(event, from_block=4)

    assert event_filter == "filter"
    assert event.calls == [{"from_block": 4}]


def test_provider_teardown_error_detection_is_narrow(monkeypatch):
    teardown_error = AttributeError("'NoneType' object has no attribute '_is_batching'")

    monkeypatch.setattr("brownie.network.event.web3.provider", None)
    assert _is_provider_teardown_error(teardown_error) is True
    assert _is_provider_teardown_error(AttributeError("unrelated")) is False

    monkeypatch.setattr("brownie.network.event.web3.provider", object())
    assert _is_provider_teardown_error(teardown_error) is False


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
    proj = compile_source("""
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
    }""")

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
    with pytest.raises(ABIEventNotFound):
        tester.events.subscribe("InvalidEventName", callback=(lambda x: x))


def test_cannot_subscribe_to_event_with_invalid_callback(tester: Contract):
    with pytest.raises(TypeError):
        tester.events.subscribe("Debug", callback=None)


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
        yield
        event_watcher_instance.reset()

    def test_can_subscribe_to_event_with_callback(_, tester: Contract):
        expected_num: int = round(time.time()) % 100  # between 0 and 99
        received_num: int = -1
        callback_was_triggered = ThreadEvent()

        def _callback(data):
            nonlocal received_num
            received_num = data["args"]["num"]
            callback_was_triggered.set()

        tester.events.subscribe("IndexedEvent", callback=_callback, delay=0.05)
        wait_for_tx(tester.emitEvents("", expected_num))

        assert callback_was_triggered.wait(1.0) is True, "Callback was not triggered."
        assert expected_num == received_num, "Callback was not triggered with the right event"

    def test_can_subscribe_to_event_with_multiple_callbacks(_, tester: Contract):
        callback_trigger_1 = ThreadEvent()
        callback_trigger_2 = ThreadEvent()

        def _cb1(_):
            callback_trigger_1.set()

        def _cb2(_):
            callback_trigger_2.set()

        tester.events.subscribe("IndexedEvent", callback=_cb1, delay=0.05)
        tester.events.subscribe("IndexedEvent", callback=_cb2, delay=0.05)
        wait_for_tx(tester.emitEvents("", 0))

        assert callback_trigger_1.wait(1.0) is True, "Callback 1 was not triggered"
        assert callback_trigger_2.wait(1.0) is True, "Callback 2 was not triggered"

    def test_callback_can_be_triggered_multiple_times(_, tester: Contract):
        callback_trigger_count = 0
        expected_callback_trigger_count = 2
        callbacks_triggered = ThreadEvent()
        callback_lock = Lock()

        def _cb(_):
            nonlocal callback_trigger_count
            with callback_lock:
                callback_trigger_count += 1
                if callback_trigger_count == expected_callback_trigger_count:
                    callbacks_triggered.set()

        tester.events.subscribe("Debug", callback=_cb, delay=0.05)
        wait_for_tx(tester.emitEvents("", 0))

        assert callbacks_triggered.wait(1.0) is True
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
        callback_triggered = ThreadEvent()

        def _cb(_):
            nonlocal trigger_count
            trigger_count += 1
            callback_triggered.set()

        event_watcher.add_event_callback(
            event=tester.events.IndexedEvent, callback=_cb, delay=0.05, repeat=False
        )

        wait_for_tx(tester.emitEvents("", 0))
        assert callback_triggered.wait(1.0) is True
        callback_triggered.clear()
        wait_for_tx(tester.emitEvents("", 0))
        wait_for_no_callback(callback_triggered)

        assert trigger_count == expected_trigger_count

    def test_can_set_both_repeating_and_not_repeating_callback_on_the_same_event(
        _, tester: Contract
    ):
        expected_trigger_count: int = 3
        trigger_count: int = 0
        callbacks_triggered = ThreadEvent()
        callback_lock = Lock()

        def _cb(_):
            nonlocal trigger_count
            with callback_lock:
                trigger_count += 1
                if trigger_count == expected_trigger_count:
                    callbacks_triggered.set()

        event_watcher.add_event_callback(
            event=tester.events.IndexedEvent, callback=_cb, delay=0.05, repeat=False
        )
        event_watcher.add_event_callback(
            event=tester.events.IndexedEvent, callback=_cb, delay=0.05, repeat=True
        )

        wait_for_tx(tester.emitEvents("", 0))
        wait_for_tx(tester.emitEvents("", 0))

        assert callbacks_triggered.wait(1.0) is True
        assert trigger_count == expected_trigger_count

    def test_stop_does_not_hang_when_event_poll_is_blocked(
        _, event_watcher_instance: EventWatcher, monkeypatch
    ):
        watch_data = _BlockingEventWatchData()
        old_thread = None
        try:
            old_thread = start_watcher_with_target(event_watcher_instance, watch_data)
            monkeypatch.setattr("brownie.network.event._WATCHER_THREAD_JOIN_TIMEOUT", 0.01)

            start_time = time.time()
            with pytest.warns(RuntimeWarning, match="Event watcher thread did not exit"):
                event_watcher_instance.stop(wait=True)

            assert time.time() - start_time < 0.5
        finally:
            if old_thread is not None:
                release_and_join_watcher(watch_data, old_thread)
            event_watcher_instance._setup()

        assert old_thread is not None
        assert old_thread.is_alive() is False

    def test_polling_does_not_hold_target_list_lock(_, event_watcher_instance: EventWatcher):
        watch_data = _BlockingEventWatchData()
        old_thread = None
        registration_thread = None
        registration_finished = ThreadEvent()
        registration_errors = []

        def register_callback():
            try:
                event_watcher_instance.add_event_callback(
                    event=_FakeEvent, callback=(lambda _: None), delay=0.05
                )
            except Exception as exc:
                registration_errors.append(exc)
            finally:
                registration_finished.set()

        try:
            old_thread = start_watcher_with_target(event_watcher_instance, watch_data)
            registration_thread = Thread(target=register_callback)
            registration_thread.start()

            assert registration_finished.wait(0.5) is True
            registration_thread.join(timeout=1.0)
            assert registration_thread.is_alive() is False
            assert registration_errors == []
            assert len(watch_data.callbacks) == 2
        finally:
            if old_thread is not None:
                event_watcher_instance.stop(wait=False)
                release_and_join_watcher(watch_data, old_thread)
            if registration_thread is not None:
                registration_thread.join(timeout=1.0)
            event_watcher_instance._setup()

        assert old_thread is not None
        assert old_thread.is_alive() is False

    def test_late_old_generation_events_do_not_trigger_callbacks_after_reset(
        _, event_watcher_instance: EventWatcher, monkeypatch
    ):
        watch_data = _BlockingEventWatchData([AttributeDict({"args": {"num": 1}})])
        fresh_watch_data = _BlockingEventWatchData([AttributeDict({"args": {"num": 2}})])
        old_thread = None
        fresh_thread = None
        try:
            old_thread = start_watcher_with_target(event_watcher_instance, watch_data)
            monkeypatch.setattr("brownie.network.event._WATCHER_THREAD_JOIN_TIMEOUT", 0.01)

            with pytest.warns(RuntimeWarning, match="Event watcher thread did not exit"):
                event_watcher_instance.reset()

            release_and_join_watcher(watch_data, old_thread)

            assert old_thread.is_alive() is False
            wait_for_no_callback(watch_data.callback_triggered)

            fresh_thread = start_watcher_with_target(event_watcher_instance, fresh_watch_data)
            fresh_watch_data.release_poll.set()
            assert fresh_watch_data.callback_triggered.wait(1.0) is True
        finally:
            if old_thread is not None:
                release_and_join_watcher(watch_data, old_thread)
            if fresh_thread is not None:
                event_watcher_instance.stop(wait=False)
                release_and_join_watcher(fresh_watch_data, fresh_thread)
            event_watcher_instance._setup()

        assert fresh_thread is not None
        assert fresh_thread.is_alive() is False

    def test_stop_wait_false_requests_shutdown_without_waiting(
        _, event_watcher_instance: EventWatcher
    ):
        watch_data = _BlockingEventWatchData()
        old_thread = None
        try:
            old_thread = start_watcher_with_target(event_watcher_instance, watch_data)
            stop_event = event_watcher_instance._watcher_stop_event

            start_time = time.time()
            event_watcher_instance.stop(wait=False)

            assert time.time() - start_time < 0.5
            assert event_watcher_instance._has_started is False
            assert stop_event.is_set() is True
        finally:
            if old_thread is not None:
                release_and_join_watcher(watch_data, old_thread)
            event_watcher_instance._setup()

        assert old_thread is not None
        assert old_thread.is_alive() is False

    @pytest.mark.skip(reason="For developing purpose")
    def test_scripting(_, tester: Contract):
        pass
