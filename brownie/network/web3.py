#!/usr/bin/python3

from web3 import (
    HTTPProvider,
    IPCProvider,
    WebsocketProvider,
    Web3
)


import brownie._config
CONFIG = brownie._config.CONFIG


def connect(network):
    if network and network not in CONFIG['networks']:
        raise ValueError("Unknown network - {}".format(network))
    brownie._config.modify_network_config(network)
    if 'ws' in CONFIG['active_network']:
        web3.providers = [WebsocketProvider(CONFIG['active_network']['ws'])]
    elif 'ipc' in CONFIG['active_network']:
        web3.providers = [IPCProvider(CONFIG['active_network']['ipc'])]
    elif 'http' in CONFIG['active_network']:
        web3.providers = [HTTPProvider(CONFIG['active_network']['http'])]
    elif 'host' in CONFIG['active_network']:
        web3.providers = [HTTPProvider(CONFIG['active_network']['host'])]
    else:
        raise ValueError("No RPC connection point given in config.json")


web3 = Web3(HTTPProvider('null'))
web3._connect = connect
connect(CONFIG['active_network']['name'])