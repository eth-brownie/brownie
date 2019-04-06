#!/usr/bin/python3

import sys

import brownie._registry as _registry
from .rpc import (
    connect,
    get_rpc,
    launch_rpc
)
from .account import Accounts

_registry.add(sys.modules[__name__])

accounts = Accounts()
web3 = None

def _notify_revert():
    pass

def _notify_reset():
    pass