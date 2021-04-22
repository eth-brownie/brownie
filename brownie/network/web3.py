#!/usr/bin/python3

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional, Set

from ens import ENS
from web3 import HTTPProvider, IPCProvider
from web3 import Web3 as _Web3
from web3 import WebsocketProvider
from web3.gas_strategies.rpc import rpc_gas_price_strategy

from brownie._config import CONFIG, _get_data_folder
from brownie.convert import to_address
from brownie.exceptions import MainnetUndefined, UnsetENSName
from brownie.network.middlewares import get_middlewares

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
        self._supports_traces = None
        self._chain_id: Optional[int] = None

    def _remove_middlewares(self) -> None:
        for middleware in self._custom_middleware:
            try:
                self.middleware_onion.remove(middleware)
            except ValueError:
                pass
            middleware.uninstall()
        self._custom_middleware.clear()

    def connect(self, uri: str, timeout: int = 30) -> None:
        """Connects to a provider"""
        self._remove_middlewares()
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
            if self.isConnected():
                self.reset_middlewares()
        except Exception:
            # checking an invalid connection sometimes raises on windows systems
            pass

    def reset_middlewares(self) -> None:
        """
        Uninstall and reinject all custom middlewares.
        """
        if self.provider is None:
            raise ConnectionError("web3 is not currently connected")
        self._remove_middlewares()

        middleware_layers = get_middlewares(self, CONFIG.network_type)

        # middlewares with a layer below zero are injected
        to_inject = sorted((i for i in middleware_layers if i < 0), reverse=True)
        for layer, obj in [(k, x) for k in to_inject for x in middleware_layers[k]]:
            middleware = obj(self)
            self.middleware_onion.inject(middleware, layer=0)
            self._custom_middleware.add(middleware)

        # middlewares with a layer of zero or greater are added
        to_add = sorted(i for i in middleware_layers if i >= 0)
        for layer, obj in [(k, x) for k in to_add for x in middleware_layers[k]]:
            middleware = obj(self)
            self.middleware_onion.add(middleware)
            self._custom_middleware.add(middleware)

    def disconnect(self) -> None:
        """Disconnects from a provider"""
        if self.provider:
            self.provider = None
            self._genesis_hash = None
            self._chain_uri = None
            self._supports_traces = None
            self._chain_id = None
            self._remove_middlewares()

    def isConnected(self) -> bool:
        if not self.provider:
            return False
        return super().isConnected()

    @property
    def supports_traces(self) -> bool:
        if not self.provider:
            return False

        # Send a malformed request to `debug_traceTransaction`. If the error code
        # returned is -32601 "endpoint does not exist/is not available" we know
        # traces are not possible. Any other error code means the endpoint is open.
        if self._supports_traces is None:
            response = self.provider.make_request("debug_traceTransaction", [])
            self._supports_traces = bool(response["error"]["code"] != -32601)

        return self._supports_traces

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
            self._genesis_hash = self.eth.get_block(0)["hash"].hex()[2:]
        return self._genesis_hash

    @property
    def chain_uri(self) -> str:
        if self.provider is None:
            raise ConnectionError("web3 is not currently connected")
        if self.genesis_hash not in _chain_uri_cache:
            block_number = max(self.eth.block_number - 16, 0)
            block_hash = self.eth.get_block(block_number)["hash"].hex()[2:]
            chain_uri = f"blockchain://{self.genesis_hash}/block/{block_hash}"
            _chain_uri_cache[self.genesis_hash] = chain_uri
        return _chain_uri_cache[self.genesis_hash]

    @property
    def chain_id(self) -> int:
        # chain ID is needed each time we a sign a transaction, however we
        # cache it after the first request to avoid redundant RPC calls
        if self.provider is None:
            raise ConnectionError("web3 is not currently connected")
        if self._chain_id is None:
            self._chain_id = self.eth.chain_id
        return self._chain_id


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
web3.eth.set_gas_price_strategy(rpc_gas_price_strategy)

try:
    with _get_path().open() as fp:
        _ens_cache: Dict = json.load(fp)
except (FileNotFoundError, json.decoder.JSONDecodeError):
    _ens_cache = {}
