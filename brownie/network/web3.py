#!/usr/bin/python3

from pathlib import Path
from web3 import (
    HTTPProvider,
    IPCProvider,
    WebsocketProvider,
    Web3 as _Web3
)

from brownie.types.types import _Singleton


class Web3(_Web3, metaclass=_Singleton):

    '''Singleton version of web3.py's Web3.'''

    def __init__(self):
        super().__init__(HTTPProvider('null'))
        self.providers.clear()

    def connect(self, uri):
        '''Connects to a provider'''
        if Path(uri).exists():
            self.providers = [IPCProvider(uri)]
        elif uri[:3] == "ws:":
            self.providers = [WebsocketProvider(uri)]
        elif uri[:4] == "http":
            self.providers = [HTTPProvider(uri)]
        else:
            raise ValueError(
                "Unknown URI - must be a path to an IPC socket, a websocket "
                "beginning with 'ws' or a URL beginning with 'http'"
            )

    def disconnect(self):
        '''Disconnects from a provider'''
        self.providers.clear()
