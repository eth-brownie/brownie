#!/usr/bin/python3

import os
from pathlib import Path

from web3 import HTTPProvider, IPCProvider
from web3 import Web3 as _Web3
from web3 import WebsocketProvider

from brownie._config import CONFIG
from brownie._singleton import _Singleton


def _expand_environment_args(uri: str) -> str:
    if "$" not in uri:
        return uri
    expanded = os.path.expandvars(uri)
    if uri != expanded:
        return expanded
    raise ValueError(f"Unable to expand environment variable in host setting: '{uri}'")


class Web3(_Web3, metaclass=_Singleton):

    """Singleton version of web3.py's Web3."""

    def __init__(self) -> None:
        super().__init__(HTTPProvider("null"))
        self.provider = None
        self._mainnet_w3 = None

    def connect(self, uri: str) -> None:
        """Connects to a provider"""
        uri = _expand_environment_args(uri)
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

    @property
    def _mainnet(self) -> _Web3:
        if CONFIG["active_network"]["name"] == "mainnet":
            return self
        if "mainnet" not in CONFIG["network"]["networks"]:
            raise ValueError("No 'mainnet' network defined in brownie-config.json")
        if not self._mainnet_w3:
            uri = _expand_environment_args(CONFIG["network"]["networks"]["mainnet"]["host"])
            self._mainnet_w3 = _Web3(HTTPProvider(uri))
        return self._mainnet_w3
