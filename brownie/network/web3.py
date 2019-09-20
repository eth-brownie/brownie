#!/usr/bin/python3

import os
from pathlib import Path
from typing import Dict

from ens import ENS
from web3 import HTTPProvider, IPCProvider
from web3 import Web3 as _Web3
from web3 import WebsocketProvider

from brownie._config import CONFIG
from brownie.convert import to_address
from brownie.exceptions import MainnetUndefined, UnsetENSName

_ens_cache: Dict = {}


class Web3(_Web3):

    """Brownie Web3 subclass"""

    def __init__(self) -> None:
        super().__init__(HTTPProvider("null"))
        self.provider = None
        self._mainnet_w3 = None

    def connect(self, uri: str) -> None:
        """Connects to a provider"""
        uri = _expand_environment_vars(uri)
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
            raise MainnetUndefined("No 'mainnet' network defined in brownie-config.json")
        if not self._mainnet_w3:
            uri = _expand_environment_vars(CONFIG["network"]["networks"]["mainnet"]["host"])
            self._mainnet_w3 = _Web3(HTTPProvider(uri))
        return self._mainnet_w3


def _expand_environment_vars(uri: str) -> str:
    if "$" not in uri:
        return uri
    expanded = os.path.expandvars(uri)
    if uri != expanded:
        return expanded
    raise ValueError(f"Unable to expand environment variable in host setting: '{uri}'")


def _resolve_address(address: str) -> str:
    if not isinstance(address, str) or "." not in address:
        return to_address(address)
    address = address.lower()
    if address not in _ens_cache:
        try:
            ns = ENS.fromWeb3(web3._mainnet)
        except MainnetUndefined as e:
            raise MainnetUndefined(f"Cannot resolve ENS address - {e}") from None
        resolved_address = ns.address(address)
        _ens_cache[address] = resolved_address
    if _ens_cache[address] is None:
        raise UnsetENSName(f"ENS address '{address}' is not set")
    return _ens_cache[address]


web3 = Web3()
