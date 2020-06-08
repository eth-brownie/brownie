#!/usr/bin/python3

import json
import os
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

from ens import ENS
from web3 import HTTPProvider, IPCProvider
from web3 import Web3 as _Web3
from web3 import WebsocketProvider
from web3.exceptions import ExtraDataLengthError
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from web3.middleware import geth_poa_middleware

from brownie._config import CONFIG, _get_data_folder
from brownie.convert import to_address
from brownie.exceptions import MainnetUndefined, UnsetENSName

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
        self._custom_middleware: Set = set()

    def connect(self, uri: str, timeout: int = 30) -> None:
        """Connects to a provider"""
        for middleware in self._custom_middleware:
            self.middleware_onion.remove(middleware)
        self._custom_middleware.clear()
        self.provider = None

        uri = _expand_environment_vars(uri)
        try:
            if Path(uri).exists():
                self.provider = IPCProvider(uri, timeout=timeout)
        except OSError:
            pass

        if self.provider is None:
            if uri.startswith("ws"):
                self.provider = WebsocketProvider(uri, {"close_timeout": timeout})
            elif uri.startswith("http"):

                self.provider = HTTPProvider(uri, {"timeout": timeout})
            else:
                raise ValueError(
                    "Unknown URI - must be a path to an IPC socket, a websocket "
                    "beginning with 'ws' or a URL beginning with 'http'"
                )

        try:
            if not self.isConnected():
                return
        except Exception:
            # checking an invalid connection sometimes raises on windows systems
            return

        # add middlewares
        try:
            if "fork" in CONFIG.active_network["cmd_settings"]:
                self._custom_middleware.add(_ForkMiddleware)
                self.middleware_onion.add(_ForkMiddleware)
        except (ConnectionError, KeyError):
            pass

        try:
            self.eth.getBlock("latest")
        except ExtraDataLengthError:
            self._custom_middleware.add(geth_poa_middleware)
            self.middleware_onion.inject(geth_poa_middleware, layer=0)
        except ConnectionError:
            pass

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
        if self.isConnected() and CONFIG.active_network["id"] == "mainnet":
            return self
        try:
            mainnet = CONFIG.networks["mainnet"]
        except KeyError:
            raise MainnetUndefined("No 'mainnet' network defined") from None
        if not self._mainnet_w3:
            uri = _expand_environment_vars(mainnet["host"])
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


class _ForkMiddleware:

    """
    Web3 middleware for raising more expressive exceptions when a forked local network
    cannot access archival states.
    """

    def __init__(self, make_request: Callable, w3: _Web3):
        self.w3 = w3
        self.make_request = make_request

    def __call__(self, method: str, params: List) -> Dict:
        response = self.make_request(method, params)
        err_msg = response.get("error", {}).get("message", "")
        if (
            err_msg == "Returned error: project ID does not have access to archive state"
            or err_msg.startswith("Returned error: missing trie node")
        ):
            raise ValueError(
                "Local fork was created more than 128 blocks ago and you do not"
                " have access to archival states. Please restart your session."
            )

        return response


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
web3.eth.setGasPriceStrategy(rpc_gas_price_strategy)

try:
    with _get_path().open() as fp:
        _ens_cache: Dict = json.load(fp)
except (FileNotFoundError, json.decoder.JSONDecodeError):
    _ens_cache = {}
