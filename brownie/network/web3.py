#!/usr/bin/python3

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional

from ens import ENS
from web3 import HTTPProvider, IPCProvider
from web3 import Web3 as _Web3
from web3 import WebsocketProvider

from brownie._config import CONFIG, _get_data_folder
from brownie.convert import to_address
from brownie.exceptions import MainnetUndefined, UnsetENSName

__tracebackhide__ = True
_chain_uri_cache: Dict = {}


class Web3(_Web3):

    """Brownie Web3 subclass"""

    def __init__(self) -> None:
        super().__init__(HTTPProvider("null"))
        self.enable_unstable_package_management_api()
        self.provider = None
        self._mainnet_w3: Optional[_Web3] = None
        self._genesis_hash: Optional[str] = None
        self._chain_uri: Optional[str] = None

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
            self._chain_uri = None

    def isConnected(self) -> bool:
        if not self.provider:
            return False
        return super().isConnected()

    @property
    def _mainnet(self) -> _Web3:
        # a web3 instance connected to the mainnet
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
        """The genesis hash of the currently active network."""
        if self.provider is None:
            raise ConnectionError("web3 is not currently connected")
        if self._genesis_hash is None:
            self._genesis_hash = self.eth.getBlock(0)["hash"].hex()[2:]
        return self._genesis_hash

    @property
    def chain_uri(self) -> str:
        if self.provider is None:
            raise ConnectionError("web3 is not currently connected")
        if self.genesis_hash not in _chain_uri_cache:
            block_number = max(self.eth.blockNumber - 16, 0)
            block_hash = self.eth.getBlock(block_number)["hash"].hex()[2:]
            chain_uri = f"blockchain://{self.genesis_hash}/block/{block_hash}"
            _chain_uri_cache[self.genesis_hash] = chain_uri
        return _chain_uri_cache[self.genesis_hash]


def _expand_environment_vars(uri: str) -> str:
    if "$" not in uri:
        return uri
    expanded = os.path.expandvars(uri)
    if uri != expanded:
        return expanded
    raise ValueError(f"Unable to expand environment variable in host setting: '{uri}'")


def _get_path() -> Path:
    return _get_data_folder().joinpath("ens.json")


def _resolve_address(domain: str) -> str:
    # convert ENS domain to address
    if not isinstance(domain, str) or "." not in domain:
        return to_address(domain)
    domain = domain.lower()
    if domain not in _ens_cache or time.time() - _ens_cache[domain][1] > 86400:
        try:
            ns = ENS.fromWeb3(web3._mainnet)
        except MainnetUndefined as e:
            raise MainnetUndefined(f"Cannot resolve ENS address - {e}") from None
        address = ns.address(domain)
        _ens_cache[domain] = [address, int(time.time())]
        with _get_path().open("w") as fp:
            json.dump(_ens_cache, fp)
    if _ens_cache[domain][0] is None:
        raise UnsetENSName(f"ENS domain '{domain}' is not set")
    return _ens_cache[domain][0]


web3 = Web3()

try:
    with _get_path().open() as fp:
        _ens_cache: Dict = json.load(fp)
except (FileNotFoundError, json.decoder.JSONDecodeError):
    _ens_cache = {}
