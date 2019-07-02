#!/usr/bin/python3

'''Assertion methods for writing brownie unit tests.'''

from brownie.types import KwargTuple
from brownie.types.convert import wei
from brownie.network.transaction import VirtualMachineError

__console_dir__ = [
    'true',
    'false',
    'confirms',
    'reverts',
    'event_fired',
    'event_not_fired',
    'equal',
    'not_equal'
]


def true(statement, fail_msg="Expected statement to be True"):
    '''Expects an object or statement to evaluate True.

    Args:
        statement: The object or statement to check.
        fail_msg: Message to show if the check fails.'''
    if statement and statement is not True:
        raise AssertionError(fail_msg+" (evaluated truthfully but not True)")
    if not statement:
        raise AssertionError(fail_msg)


def false(statement, fail_msg="Expected statement to be False"):
    '''Expects an object or statement to evaluate False.

    Args:
        statement: The object or statement to check.
        fail_msg: Message to show if the check fails.'''
    if not statement and statement is not False:
        raise AssertionError(fail_msg+" (evaluated falsely but not False)")
    if statement:
        raise AssertionError(fail_msg)


def confirms(fn, args, fail_msg="Expected transaction to confirm"):
    '''Expects a transaction to confirm.

    Args:
        fn: ContractTx instance to call.
        args: List or tuple of contract input args.
        fail_msg: Message to show if the check fails.

    Returns:
        TransactionReceipt instance.'''
    try:
        tx = fn(*args)
    except VirtualMachineError as e:
        raise AssertionError(f"{fail_msg}\n  {e.source}")
    return tx


def reverts(fn, args, revert_msg=None):
    '''Expects a transaction to revert.

    Args:
        fn: ContractTx instance to call.
        args: List or tuple of contract input args.
        fail_msg: Message to show if the check fails.
        revert_msg: If set, the check only passes if the returned
                    revert message matches the given one.'''
    try:
        fn(*args)
    except VirtualMachineError as e:
        if not revert_msg or revert_msg == e.revert_msg:
            return
        raise AssertionError(f"Reverted with '{e.revert_msg}', expected '{revert_msg}'\n{e.source}")
    raise AssertionError("Expected transaction to revert")


def event_fired(tx, name, count=None, values=None):
    '''Expects a transaction to contain an event.

    Args:
        tx: A TransactionReceipt.
        name: Name of the event expected to fire.
        count: Number of times the event should fire. If left as None,
               the event is expected to fire one or more times.
        values: A dict or list of dicts of {key:value} that must match
                against the fired events with the given name. The length of
                values must also match the number of events that fire.'''
    if values is not None:
        if type(values) is dict:
            values = [values]
        if type(values) not in (tuple, list):
            raise TypeError("Event values must be given as a dict or list of dicts.")
    if count is not None:
        if values is not None and len(values) != count:
            raise ValueError("Required count does not match length of required values.")
        if count != tx.events.count(name):
            raise AssertionError(
                f"Event {name} - expected {count} events to fire, got {tx.events.count(name)}"
            )
    elif count is None and not tx.events.count(name):
        raise AssertionError(f"Expected event '{name}' to fire")
    if values is None:
        return
    for i in range(len(values)):
        for k, v in values[i].items():
            event = tx.events[name][i]
            if k not in event:
                raise AssertionError(f"Event '{name}' does not contain value '{k}'")
            if event[k] != v:
                raise AssertionError(f"Event {name} - expected '{k}' to equal {v}, got {event[k]}")


def event_not_fired(tx, name, fail_msg="Expected event not to fire"):
    '''Expects a transaction not to contain an event.

    Args:
        tx: A TransactionReceipt.
        name: Name of the event expected to fire.
        fail_msg: Message to show if check fails.'''
    if name in tx.events:
        raise AssertionError(fail_msg)


def equal(a, b, fail_msg="Expected values to be equal", strict=False):
    '''Expects two values to be equal.

    Args:
        a: First value.
        b: Second value.
        fail_msg: Message to show if check fails.'''
    if not _compare_input(a, b, strict):
        raise AssertionError(f"{fail_msg}: {a} != {b}")


def not_equal(a, b, fail_msg="Expected values to be not equal", strict=False):
    '''Expects two values to be not equal.

    Args:
        a: First value.
        b: Second value.
        fail_msg: Message to show if check fails.'''
    if _compare_input(a, b, strict):
        raise AssertionError(f"{fail_msg}: {a} == {b}")


def _compare_input(a, b, strict=False):
    if type(a) not in (tuple, list, KwargTuple):
        types_ = set([type(a), type(b)])
        if dict in types_:
            return a == b
        if strict or types_.intersection([bool, type(None)]):
            return a is b
        return _convert_str(a) == _convert_str(b)
    if type(b) not in (tuple, list, KwargTuple) or len(b) != len(a):
        return False
    return next((False for i in range(len(a)) if not _compare_input(a[i], b[i], strict)), True)


def _convert_str(value):
    if type(value) is not str:
        if not hasattr(value, 'address'):
            return value
        value = value.address
    if value.startswith('0x'):
        return "0x" + value.lstrip('0x').lower()
    if value.count(" ") != 1:
        return value
    try:
        return wei(value)
    except ValueError:
        return value
