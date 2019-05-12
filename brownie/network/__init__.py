#!/usr/bin/python3

import sys as _sys

from .web3 import Web3 as _Web3
from .rpc import Rpc as _Rpc
from .account import Accounts as _Accounts
from .history import TxHistory as _TxHistory
from brownie._config import CONFIG, modify_network_config


__all__ = ['accounts', 'history', 'network', 'rpc', 'web3']

network = _sys.modules[__name__]
accounts = _Accounts()
rpc = _Rpc()
history = _TxHistory()
web3 = _Web3()


def connect(network=None):
    '''Connects to the network.

    Args:
        network: string of of the name of the network to connect to

    Network information is retrieved from brownie-config.json'''
    if CONFIG['active_network']['name']:
        raise ConnectionError("Already connected to network '{}'".format(
            CONFIG['active_network']['name']
        ))
    try:
        modify_network_config(network or CONFIG['network_defaults']['name'])
        if 'host' not in CONFIG['active_network']:
            raise KeyError(
                "No host given in brownie-config.json for network"
                " '{}'".format(CONFIG['active_network']['name'])
            )
        web3.connect(CONFIG['active_network']['host'])
        if 'test-rpc' in CONFIG['active_network'] and not rpc.is_active():
            if is_connected():
                if web3.eth.blockNumber != 0:
                    raise ValueError("Local RPC Client has a block height > 0")
                rpc.attach(CONFIG['active_network']['host'])
            else:
                rpc.launch(CONFIG['active_network']['test-rpc'])
    except Exception:
        CONFIG['active_network']['name'] = None
        raise


def disconnect():
    '''Disconnects from the network.'''
    web3.disconnect()
    if rpc.is_active():
        if rpc.is_child():
            rpc.kill()
        else:
            rpc.reset()
    CONFIG['active_network']['name'] = None


def show_active():
    '''Returns the name of the currently active network'''
    if not web3.providers:
        return None
    return CONFIG['active_network']['name']


def is_connected():
    '''Returns a bool indicating if the Web3 object is currently connected'''
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
