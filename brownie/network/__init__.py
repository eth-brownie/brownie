#!/usr/bin/python3

import sys as _sys

from .web3 import Web3 as _Web3
from .rpc import Rpc as _Rpc
from .account import Accounts as _Accounts
from .history import TxHistory as _TxHistory
import brownie._config as _config
CONFIG = _config.CONFIG


__all__ = ['accounts', 'history', 'network', 'rpc', 'web3']

network = _sys.modules[__name__]
accounts = _Accounts()
rpc = _Rpc()
history = _TxHistory()
web3 = _Web3()


def connect(network=None):
    if CONFIG['active_network']['name']:
        raise ConnectionError("Already connected to network '{}'".format(CONFIG['active_network']['name']))
    try:
        _config.modify_network_config(network or CONFIG['network_defaults']['name'])
        if 'host' not in CONFIG['active_network']:
            raise KeyError("No host given in brownie-config.json for network '{}'".format(CONFIG['active_network']['name']))
        web3.connect(CONFIG['active_network']['host'])
        if 'test-rpc' in CONFIG['active_network'] and not rpc.is_active():
            rpc.launch(CONFIG['active_network']['test-rpc'])
    except Exception:
        CONFIG['active_network']['name'] = None
        raise


def disconnect(kill_rpc=False):
    web3.disconnect()
    if rpc.is_active():
        rpc.kill()
    CONFIG['active_network']['name'] = None


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