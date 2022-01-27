#!/usr/bin/python3

import json
import warnings
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple, Union, ValuesView, Type, Callable

import eth_event
from eth_event import EventError

from web3._utils import filters, datatypes
from web3.datastructures import AttributeDict

from brownie import web3
from brownie._config import _get_data_folder
from brownie.convert.datatypes import ReturnValue
from brownie.convert.normalize import format_event
from brownie.exceptions import EventLookupError

from . import alert
from .contract import Contract, ProjectContract
from .web3 import ContractEvent


class EventDict:
    """
    Dict/list hybrid container, base class for all events fired in a transaction.
    """

    def __init__(self, events: Optional[List] = None) -> None:
        """Instantiates the class.

        Args:
            events: event data as supplied by eth_event.decode_logs or eth_event.decode_trace"""
        if events is None:
            events = []

        self._ordered = [
            _EventItem(
                i["name"],
                i["address"],
                [OrderedDict((x["name"], x["value"]) for x in i["data"])],
                (pos,),
            )
            for pos, i in enumerate(events)
        ]

        self._dict: Dict = OrderedDict()
        for event in self._ordered:
            if event.name not in self._dict:
                events = [i for i in self._ordered if i.name == event.name]
                self._dict[event.name] = _EventItem(
                    event.name, None, events, tuple(i.pos[0] for i in events)
                )

    def __repr__(self) -> str:
        return str(self)

    def __bool__(self) -> bool:
        return bool(self._ordered)

    def __contains__(self, name: str) -> bool:
        """returns True if an event fired with the given name."""
        return name in [i.name for i in self._ordered]

    def __getitem__(self, key: Union[str, int]) -> "_EventItem":
        """if key is int: returns the n'th event that was fired
        if key is str: returns a _EventItem dict of all events where name == key"""
        if not isinstance(key, (int, str)):
            raise TypeError(f"Invalid key type '{type(key)}' - can only use strings or integers")
        if isinstance(key, int):
            try:
                return self._ordered[key]
            except IndexError:
                raise EventLookupError(
                    f"Index out of range - only {len(self._ordered)} events fired"
                )
        if key in self._dict:
            return self._dict[key]
        raise EventLookupError(f"Event '{key}' did not fire.")

    def __iter__(self) -> Iterator:
        return iter(self._ordered)

    def __len__(self) -> int:
        """returns the number of events that fired."""
        return len(self._ordered)

    def __str__(self) -> str:
        return str(dict((k, [i[0] for i in v._ordered]) for k, v in self._dict.items()))

    def count(self, name: str) -> int:
        """EventDict.count(name) -> integer -- return number of occurrences of name"""
        return len([i.name for i in self._ordered if i.name == name])

    def items(self) -> List:
        """EventDict.items() -> a list object providing a view on EventDict's items"""
        return list(self._dict.items())

    def keys(self) -> List:
        """EventDict.keys() -> a list object providing a view on EventDict's keys"""
        return list(self._dict.keys())

    def values(self) -> ValuesView:
        """EventDict.values() -> a list object providing a view on EventDict's values"""
        return self._dict.values()


class _EventItem:
    """
    Dict/list hybrid container, represents one or more events with the same name
    that were fired in a transaction.

    Attributes
    ----------
    name : str
        Name of the event.
    address : str
        Address where this event fired. When the object represents more than one event,
        this value is set to `None`.
    pos : tuple
        Tuple of indexes where this event fired.
    """

    def __init__(self, name: str, address: Optional[str], event_data: List, pos: Tuple) -> None:
        self.name = name
        self.address = address
        self._ordered = event_data
        self.pos = pos

    def __getitem__(self, key: Union[int, str]) -> List:
        """if key is int: returns the n'th event that was fired with this name
        if key is str: returns the value of data field 'key' from the 1st event
        within the container"""
        if not isinstance(key, (int, str)):
            raise TypeError(f"Invalid key type '{type(key)}' - can only use strings or integers")
        if isinstance(key, int):
            try:
                return self._ordered[key]
            except IndexError:
                raise EventLookupError(
                    f"Index out of range - only {len(self._ordered)} '{self.name}' events fired"
                )
        if key in self._ordered[0]:
            return self._ordered[0][key]
        if f"{key} (indexed)" in self._ordered[0]:
            return self._ordered[0][f"{key} (indexed)"]
        valid_keys = ", ".join(self.keys())
        raise EventLookupError(
            f"Unknown key '{key}' - the '{self.name}' event includes these keys: {valid_keys}"
        )

    def __contains__(self, name: str) -> bool:
        """returns True if this event contains a value with the given name."""
        return name in self._ordered[0]

    def __len__(self) -> int:
        """returns the number of events held in this container."""
        return len(self._ordered)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        if len(self._ordered) == 1:
            return str(self._ordered[0])
        return str([i[0] for i in self._ordered])

    def __iter__(self) -> Iterator:
        return iter(self._ordered)

    def __eq__(self, other: object) -> bool:
        if len(self._ordered) == 1:
            if isinstance(other, (tuple, list, ReturnValue)):
                # sequences compare directly against the event values
                return self._ordered[0].values() == other
            return other == self._ordered[0]
        return other == self._ordered

    def items(self) -> ReturnValue:
        """_EventItem.items() -> a list object providing a view on _EventItem[0]'s items"""
        return ReturnValue([(i, self[i]) for i in self.keys()])

    def keys(self) -> ReturnValue:
        """_EventItem.keys() -> a list object providing a view on _EventItem[0]'s keys"""
        return ReturnValue([i.replace(" (indexed)", "") for i in self._ordered[0].keys()])

    def values(self) -> ReturnValue:
        """_EventItem.values() -> a list object providing a view on _EventItem[0]'s values"""
        return ReturnValue(self._ordered[0].values())


# class EventSubscriber:
#     # Member variables
#     _contract: Contract = None
#     _alert: alert.Alert = None
#     _event_name: str = None
#     _callback: Callable[[AttributeDict, AttributeDict], None] = None
#     _gen_event_getter = None  # generator
#     _from_block: int = 0

#     def __init__(
#         self, contract: Contract, event_name: str, callback: Callable, **kwargs
#     ):
#         """Initializes instance of the EventSubscriber class.

#         Args:
#             contract (Contract): Contract from which to get the event.
#             event_name (str): Event name in the solidity file
#             callback (Callable): Function called on event received. It must take 2 parameters.
#             The first one is useless, and the second one is a 'web3.datastructures.AttributeDict'
#             object containing the event data.

#         **kwargs:
#             from_block (int > 0): Block from which to start catching events.
#             auto_enable (bool): If False, does not enable the callback after instantiation,
#             otherwise, calls the 'enable' function with the default parameters

#         Raises:
#             TypeError: Raised when the 'contract' argument is not of
#             type brownie.network.contract.Contract or of type brownie.network.contract.ProjectContract
#         """
#         if type(contract) not in [Contract, ProjectContract]:
#             raise TypeError("Given argument 'contract' invalid type.")
#         self._contract = contract
#         self._event_name = event_name
#         self._callback = callback
#         self._from_block = kwargs.get("from_block", web3.eth.block_number)

#     def enable(self, delay: float = 2.0, repeat: bool = False):
#         """Enables the established callback on the established event.

#         Args:
#             delay (float, optional): @dev see : https://eth-brownie.readthedocs.io/en/stable/api-network.html#brownie.network.alert.Alert. Defaults to 2.
#             repeat (bool, optional): @dev see : https://eth-brownie.readthedocs.io/en/stable/api-network.html#brownie.network.alert.Alert. Defaults to False.

#         Returns:
#             self [EventSubscriber]: Class current instance.
#         """
#         self.__setup_event_callback(delay, repeat)
#         return self

#     def disable(self, wait: bool = False):
#         """Disables the established callback on the established event.

#         Args:
#             wait (bool, optional): @dev see : https://eth-brownie.readthedocs.io/en/stable/api-network.html#Alert.stop. Defaults to False.
#         """
#         if self._alert == None or self._alert.is_alive() == False:
#             print("Warning : Alert not enabled.")
#             return
#         while self._alert.is_alive():
#             self._alert.stop(wait)

#     def wait(
#         self,
#         occurence_nb: int = 1,
#         timeout: int = None,
#         disable_on_completed: bool = False,
#     ):
#         """Waits for the watched event to occur 'occurence_nb' times.

#         Args:
#             occurence_nb (int, optional): Number of occurence to wait for. Defaults to 1.
#             timeout (int, optional): Number of seconds to wait before timing out while waiting for an event. Defaults to None.

#         Returns:
#             self [EventSubscriber]: Class current instance.
#         """
#         for _ in range(occurence_nb):
#             self._alert.wait(timeout)
#         if disable_on_completed == True:
#             self.disable(False)
#         return self

#     def is_alive(self):
#         return self._alert.is_alive()

#     # PRIVATE METHODS #

#     def __setup_event_callback(self, _delay: float, _repeat: bool):
#         # Get event (ContractEvent) from event name
#         self.event_watched = self._contract.events[self._event_name]
#         # Get event generator
#         self._gen_event_getter = _get_next_event(
#             self.event_watched, from_block=self._from_block
#         )
#         # Creates a new alert
#         self._alert = alert.new(
#             next,
#             args=(self._gen_event_getter,),
#             delay=_delay,
#             callback=self._callback,
#             repeat=_repeat,
#         )

#     # PROPERTIES #

#     def _get_prop_check_fact(self):
#         return self._property_checking_factory

#     def _set_prop_check_fact(self, value):
#         if type(value) != datatypes.PropertyCheckingFactory:
#             raise TypeError("event_watched fset : invalid value type. Given value type : {}".format(type(value)))
#         self._property_checking_factory = value

#     event_watched = property(
#         fget=_get_prop_check_fact, fset=_set_prop_check_fact
#     )


# def _get_latests_events(event: Type["ContractEvent"], **kwargs):
#     """Returns a generator, which, when called, returns a list containing all
#     events that occured between the last checked block (or the start block on
#     the first call) and the last mined block.

#     Args:
#         event (ContractEvent): The contract 'topic' from which to catch new events

#     Yields:
#         events: List containing all event logs since last call.
#     """
#     # Set starting blocks.
#     start_block = kwargs.get("start_block", web3.eth.block_number - 100)
#     to_block = web3.eth.block_number

#     while True:
#         event_filter: filters.LogFilter = event.createFilter(
#             fromBlock=start_block, toBlock=to_block
#         )
#         events = event_filter.get_all_entries()
#         yield events

#         # On new call, shifts the blocks to look at.
#         start_block = to_block
#         to_block = web3.eth.block_number


# def _get_next_event(event_to_watch: Type["ContractEvent"], **kwargs):
#     # Get event catcher generator
#     _gen_latests_events = _get_latests_events(event_to_watch, **kwargs)
#     while True:
#         # Get latests events as a list since last block checked
#         events_list = next(_gen_latests_events)
#         # If no event is detected return None
#         if events_list.__len__() == 0:
#             yield None
#         # Submit latest events one by one.
#         for event in events_list:
#             yield event


def __get_path() -> Path:
    return _get_data_folder().joinpath("topics.json")


def _get_topics(abi: List) -> Dict:
    topic_map = eth_event.get_topic_map(abi)

    updated_topics = _topics.copy()

    for key, value in topic_map.items():
        if key not in updated_topics:
            # new event topic
            updated_topics[key] = value
        elif value == updated_topics[key]:
            # existing event topic, nothing has changed
            continue
        elif not next((i for i in updated_topics[key]["inputs"] if i["indexed"]), False):
            # existing topic, but the old abi has no indexed events - keep the new one
            updated_topics[key] = value

    if updated_topics != _topics:
        _topics.update(updated_topics)
        with __get_path().open("w") as fp:
            json.dump(updated_topics, fp, sort_keys=True, indent=2)

    return {v["name"]: k for k, v in topic_map.items()}


def _add_deployment_topics(address: str, abi: List) -> None:
    _deployment_topics[address] = eth_event.get_topic_map(abi)


def _decode_logs(logs: List, contracts: Optional[Dict] = None) -> EventDict:
    if not logs:
        return EventDict()

    idx = 0
    events: List = []
    while True:
        address = logs[idx]["address"]
        try:
            new_idx = logs.index(next(i for i in logs[idx:] if i["address"] != address))
            log_slice = logs[idx:new_idx]
            idx = new_idx
        except StopIteration:
            log_slice = logs[idx:]

        topics_map = _deployment_topics.get(address, _topics)
        for item in log_slice:
            if contracts and contracts[item.address]:
                note = _decode_ds_note(item, contracts[item.address])
                if note:
                    events.append(note)
                    continue
            try:
                events.extend(eth_event.decode_logs([item], topics_map, allow_undecoded=True))
            except EventError as exc:
                warnings.warn(f"{address}: {exc}")

        if log_slice[-1] == logs[-1]:
            break

    events = [format_event(i) for i in events]
    return EventDict(events)


def _decode_ds_note(log, contract):  # type: ignore
    # ds-note encodes function selector as the first topic
    selector, tail = log.topics[0][:4], log.topics[0][4:]
    if selector.hex() not in contract.selectors or sum(tail):
        return
    name = contract.selectors[selector.hex()]
    data = bytes.fromhex(log.data[2:])
    # data uses ABI encoding of [uint256, bytes] or [bytes] in different versions
    # instead of trying them all, assume the payload starts from selector
    try:
        func, args = contract.decode_input(data[data.index(selector) :])
    except ValueError:
        return
    return {
        "name": name,
        "address": log.address,
        "decoded": True,
        "data": [
            {"name": abi["name"], "type": abi["type"], "value": arg, "decoded": True}
            for arg, abi in zip(args, contract.get_method_object(selector.hex()).abi["inputs"])
        ],
    }


def _decode_trace(trace: Sequence, initial_address: str) -> EventDict:
    if not trace:
        return EventDict()

    events = eth_event.decode_traceTransaction(
        trace, _topics, allow_undecoded=True, initial_address=initial_address
    )
    events = [format_event(i) for i in events]
    return EventDict(events)


# dictionary of event topic ABIs specific to a single contract deployment
_deployment_topics: Dict = {}

# general event topic ABIs for decoding events on unknown contracts
_topics: Dict = {}

try:
    with __get_path().open() as fp:
        _topics = json.load(fp)
except (FileNotFoundError, json.decoder.JSONDecodeError):
    pass
