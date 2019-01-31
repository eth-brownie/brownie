#!/usr/bin/python3

from lib.components.eth import wei
from lib.components.transaction import VirtualMachineError

def true(statement, fail_msg="Expected statement to be true"):
    if not statement:
        raise AssertionError(fail_msg)

def false(statement, fail_msg="Expected statement to be False"):
    if statement:
        raise AssertionError(fail_msg)

def reverts(fn, args, fail_msg="Expected transaction to revert", revert_msg=None):
    try: 
        tx = fn(*args)
    except VirtualMachineError as e:
        if not revert_msg or revert_msg == e.revert_msg:
            return
    if not tx.status and (not revert_msg or revert_msg == tx.revert_msg):
        return
    raise AssertionError(fail_msg)

def confirms(fn, args, fail_msg="Expected transaction to confirm"):
    try:
        return fn(*args)
    except VirtualMachineError:
        raise AssertionError(fail_msg)

def _convert(a, b):
    try: a = wei(a)
    except ValueError: pass
    try: b = wei(b)
    except ValueError: pass
    return a, b

def equal(a, b, fail_msg="Expected values to be equal"):
    a, b = _convert(a, b)
    if a != b:
        raise AssertionError(fail_msg+": {} != {}".format(a,b))

def not_equal(a, b, fail_msg="Expected values to be not equal"):
    a, b = _convert(a, b)
    if a == b:
        raise AssertionError(fail_msg+": {} == {}".format(a,b))