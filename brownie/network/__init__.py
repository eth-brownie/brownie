#!/usr/bin/python3

import sys as _sys

from .web3 import web3
from .rpc import Rpc as _Rpc
from .account import Accounts as _Accounts
from .history import history
import brownie._registry as _registry
import brownie._config as _config
CONFIG = _config.CONFIG


__all__ = ['accounts', 'history', 'network', 'rpc', 'web3']

network = _sys.modules[__name__]
accounts = _Accounts()
rpc = _Rpc(web3)

def connect(network=None, launch_rpc=False):
    if network is None:
        network = CONFIG['network_defaults']['name']
    web3._connect(network)
    if launch_rpc and 'test-rpc' in CONFIG['active_network']:
        rpc.launch()
    else:
        _registry.reset()


def disconnect(kill_rpc=False):
    web3.providers.clear()
    if kill_rpc and rpc.is_active():
        rpc.kill()
    else:
        _registry.reset()


def reset(network=None):
    '''Reboots the local RPC client and resets the brownie environment.

    Args:
        network (string): Name of the new network to switch to.'''
    if not network:
        network = CONFIG['active_network']['name']
    if network not in CONFIG['networks']:
        raise ValueError("Unknown network - {}".format(network))
    reset_rpc = rpc.is_active()
    disconnect(reset_rpc)
    connect(network, reset_rpc)


def show_active():
    if not web3.providers:
        return None
    return CONFIG['active_network']['name']


def is_connected():
    return web3.isConnected()


def gas_limit(*args):
    '''Displays or modifies the default gas limit.

    * If no argument is given, the current default is displayed.
    * If an integer value is given, this will be the default gas limit.
    * If set to "auto", None, True or False, the gas limit is determined
    automatically.'''
    if args:
        if args[0] in ("auto", None, False, True):
            CONFIG['active_network']['gas_limit'] = False
        else:
            try:
                CONFIG['active_network']['gas_limit'] = int(args[0])
            except Exception:
                return "Invalid gas limit."
    return "Gas limit is set to {}".format(
        CONFIG['active_network']['gas_limit'] or "automatic"
    )