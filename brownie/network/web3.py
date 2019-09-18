#!/usr/bin/python3

from pathlib import Path

from web3 import HTTPProvider, IPCProvider
from web3 import Web3 as _Web3
from web3 import WebsocketProvider

from brownie._singleton import _Singleton


class Web3(_Web3, metaclass=_Singleton):

    """Singleton version of web3.py's Web3."""

    def __init__(self) -> None:
        super().__init__(HTTPProvider("null"))
        self.provider = None

    def connect(self, uri: str) -> None:
        """Connects to a provider"""
        try:
            if Path(uri).exists():
                self.provider = IPCProvider(uri)
                return
        except OSError:
            pass
        if uri[:3] == "ws:":
            self.provider = WebsocketProvider(uri)
        elif uri[:4] == "http":
            self.provider = HTTPProvider(uri)
        else:
            raise ValueError(
                "Unknown URI - must be a path to an IPC socket, a websocket "
                "beginning with 'ws' or a URL beginning with 'http'"
            )

    def disconnect(self) -> None:
        """Disconnects from a provider"""
        if self.provider:
            self.provider = None

    def isConnected(self) -> bool:
        if not self.provider:
            return False
        return super().isConnected()
