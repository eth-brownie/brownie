#!/usr/bin/python3

from typing import Optional, Tuple, Union

from brownie import project
from brownie._config import CONFIG, _modify_network_config
from brownie.convert import Wei

from .account import Accounts
from .rpc import Rpc, _notify_registry
from .web3 import web3

rpc = Rpc()


def connect(network: str = None, launch_rpc: bool = True) -> None:
    """Connects to the network.

    Args:
        network: string of of the name of the network to connect to

    Network information is retrieved from brownie-config.json"""
    if is_connected():
        raise ConnectionError(f"Already connected to network '{CONFIG['active_network']['name']}'")
    try:
        active = _modify_network_config(network or CONFIG["network"]["default"])
        if "host" not in active:
            raise KeyError(f"No host in brownie-config.json for network '{active['name']}'")
        host = active["host"]

        if ":" not in host.split("//", maxsplit=1)[-1]:
            try:
                host += f":{active['test_rpc']['port']}"
            except KeyError:
                pass

        web3.connect(host)
        if "test_rpc" in active and launch_rpc and not rpc.is_active():
            if is_connected():
                if web3.eth.blockNumber != 0:
                    raise ValueError("Local RPC Client has a block height > 0")
                rpc.attach(host)
            else:
                rpc.launch(**active["test_rpc"])
        else:
            Accounts()._reset()
        if CONFIG["active_network"]["persist"]:
            for p in project.get_loaded_projects():
                p._load_deployments()

    except Exception:
        CONFIG["active_network"] = {"name": None}
        web3.disconnect()
        raise


def disconnect(kill_rpc: bool = True) -> None:
    """Disconnects from the network."""
    if not is_connected():
        raise ConnectionError("Not connected to any network")
    CONFIG["active_network"] = {"name": None}
    if kill_rpc and rpc.is_active():
        if rpc.is_child():
            rpc.kill()
        else:
            rpc.reset()
    web3.disconnect()
    _notify_registry(0)


def show_active() -> Optional[str]:
    """Returns the name of the currently active network"""
    if not web3.provider:
        return None
    return CONFIG["active_network"]["name"]


def is_connected() -> bool:
    """Returns a bool indicating if the Web3 object is currently connected"""
    return web3.isConnected()


def gas_limit(*args: Tuple[Union[int, str, bool, None]]) -> Union[int, bool]:
    """Gets and optionally sets the default gas limit.

    * If an integer value is given, this will be the default gas limit.
    * If set to 'auto', the gas limit is determined automatically."""

    if not is_connected():
        raise ConnectionError("Not connected to any network")
    if args:
        if args[0] in (None, False, True, "auto"):
            CONFIG["active_network"]["gas_limit"] = False
        else:
            try:
                limit: int = int(args[0])  # type: ignore
            except ValueError:
                raise TypeError(f"Invalid gas limit '{args[0]}'")
            if limit < 21000:
                raise ValueError("Minimum gas limit is 21000")
            CONFIG["active_network"]["gas_limit"] = limit
    return CONFIG["active_network"]["gas_limit"]


def gas_price(*args: Tuple[Union[int, str, bool, None]]) -> Union[int, bool]:
    """Gets and optionally sets the default gas price.

    * If an integer value is given, this will be the default gas price.
    * If set to 'auto', the gas price is determined automatically."""

    if not is_connected():
        raise ConnectionError("Not connected to any network")
    if args:
        if args[0] in (None, False, True, "auto"):
            CONFIG["active_network"]["gas_price"] = False
        else:
            try:
                price = Wei(args[0])
            except ValueError:
                raise TypeError(f"Invalid gas price '{args[0]}'")
            CONFIG["active_network"]["gas_price"] = price
    return CONFIG["active_network"]["gas_price"]
