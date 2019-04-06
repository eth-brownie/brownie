#!/usr/bin/python3


import sys

from .rpc import (
    connect,
    get_rpc,
    launch_rpc
)

import brownie._registry as _registry

_registry.add(sys.modules[__name__])

def _notify():
    pass

def _notify_reset():
    pass