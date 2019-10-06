#!/usr/bin/python3

import os
from pathlib import Path
from typing import Dict, Optional

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
        self.enable_unstable_package_management_api()
        self.provider = None
        self._mainnet_w3: Optional[_Web3] = None
        self._genesis_hash: Optional[str] = None

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
            self._genesis_hash = None

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
            self._mainnet_w3.enable_unstable_package_management_api()
        return self._mainnet_w3

    @property
    def genesis_hash(self) -> str:
        if self._genesis_hash is None:
            self._genesis_hash = self.eth.getBlock(0)["hash"].hex()[2:]
        return self._genesis_hash


def _expand_environment_vars(uri: str) -> str:
    if "$" not in uri:
        return uri
    expanded = os.path.expandvars(uri)
    if uri != expanded:
        return expanded
    raise ValueError(f"Unable to expand environment variable in host setting: '{uri}'")


def _resolve_address(domain: str) -> str:
    if not isinstance(domain, str) or "." not in domain:
        return to_address(domain)
    domain = domain.lower()
    if domain not in _ens_cache:
        try:
            ns = ENS.fromWeb3(web3._mainnet)
        except MainnetUndefined as e:
            raise MainnetUndefined(f"Cannot resolve ENS address - {e}") from None
        address = ns.address(domain)
        _ens_cache[domain] = address
    if _ens_cache[domain] is None:
        raise UnsetENSName(f"ENS domain '{domain}' is not set")
    _ens_cache[address] = domain
    return _ens_cache[domain]


def _resolve_domain(address: str) -> str:
    address = to_address(address)
    if address not in _ens_cache:
        try:
            ns = ENS.fromWeb3(web3._mainnet)
        except MainnetUndefined as e:
            raise MainnetUndefined(f"Cannot resolve ENS address - {e}") from None
        domain = ns.name(address)
        _ens_cache[address] = domain
        if domain is not None:
            _ens_cache[domain] = address
    if _ens_cache[address] is None:
        raise UnsetENSName(f"Address '{address}' does not resolve to an ENS domain")
    return _ens_cache[address]


web3 = Web3()
