#!/usr/bin/python3

import sys
import time

from .web3 import web3
import brownie._registry as _registry
from .rpc import Rpc as _Rpc
from .account import Accounts as _Accounts
import brownie.config
CONFIG = brownie.config


__all__ = ['accounts', 'web3', 'rpc', 'connect', 'disconnect', 'reset']

accounts = _Accounts()
rpc = _Rpc(web3)


def connect(network, launch_rpc = False):
    web3._connect(network)
    if launch_rpc and 'test-rpc' not in CONFIG['active_network']:
        rpc.launch()
    else:
        _registry.reset()


def disconnect(kill_rpc = False):
    web3.providers.clear()
    if kill_rpc and rpc.is_active():
        rpc.kill()
    else:
        _registry.reset()


def reset(network = None, launch_rpc = False):
    '''Reboots the local RPC client and resets the brownie environment.

    Args:
        network (string): Name of the new network to switch to.'''
    if network and network not in CONFIG['networks']:
        raise ValueError("Unknown network - {}".format(network))
    disconnect(launch_rpc)
    connect(network, launch_rpc)