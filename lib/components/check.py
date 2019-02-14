#!/usr/bin/python3

'''Assertion methods for writing brownie unit tests.'''

from lib.components.eth import wei
from lib.components.transaction import VirtualMachineError
from lib.services import config
CONFIG = config.CONFIG


def true(statement, fail_msg="Expected statement to be true"):
    '''Expects an object or statement to evaluate True.
    
    Args:
        statement: The object or statement to check.
        fail_msg: Message to show if the check fails.'''
    if not statement:
        raise AssertionError(fail_msg)


def false(statement, fail_msg="Expected statement to be False"):
    '''Expects an object or statement to evaluate False.
    
    Args:
        statement: The object or statement to check.
        fail_msg: Message to show if the check fails.'''
    if statement:
        raise AssertionError(fail_msg)


def reverts(fn, args, fail_msg="Expected transaction to revert", revert_msg=None):
    '''Expects a transaction to revert.
    
    Args:
        fn: ContractTx instance to call.
        args: List or tuple of contract input args.
        fail_msg: Message to show if the check fails.
        revert_msg: If set, the check only passes if the returned revert message
                    matches the given one.'''
    try: 
        fn(*args)
    except VirtualMachineError as e:
        if not revert_msg or revert_msg == e.revert_msg:
            return
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
        raise AssertionError("{}\n  {}".format(fail_msg, e.source))
    return tx


def equal(a, b, fail_msg="Expected values to be equal"):
    '''Expects two values to be equal.

    Args:
        a: First value.
        b: Second value.
        fail_msg: Message to show if check fails.'''
    a, b = _convert(a, b)
    if a != b:
        raise AssertionError(fail_msg+": {} != {}".format(a,b))


def not_equal(a, b, fail_msg="Expected values to be not equal"):
    '''Expects two values to be not equal.

    Args:
        a: First value.
        b: Second value.
        fail_msg: Message to show if check fails.'''
    a, b = _convert(a, b)
    if a == b:
        raise AssertionError(fail_msg+": {} == {}".format(a,b))


# attempt conversion with wei before comparing equality
def _convert(a, b):
    try: a = wei(a)
    except ValueError: pass
    try: b = wei(b)
    except ValueError: pass
    return a, b