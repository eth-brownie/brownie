#!/usr/bin/python3

import warnings
from typing import Optional, Tuple, Union

from brownie import project
from brownie._config import CONFIG
from brownie.convert import Wei
from brownie.exceptions import BrownieEnvironmentWarning

from .account import Accounts
from .gas.bases import GasABC
from .rpc import Rpc
from .state import Chain, _notify_registry
from .web3 import web3

chain = Chain()
rpc = Rpc()


def connect(network: str = None, launch_rpc: bool = True) -> None:
    """Connects to the network.

    Args:
        network: string of of the name of the network to connect to

    Network information is retrieved from brownie-config.json"""
    if is_connected():
        raise ConnectionError(f"Already connected to network '{CONFIG.active_network['id']}'")
    try:
        active = CONFIG.set_active_network(network)
        host = active["host"]

        if ":" not in host.split("//", maxsplit=1)[-1]:
            try:
                host += f":{active['cmd_settings']['port']}"
            except KeyError:
                pass

        web3.connect(host, active.get("timeout", 30))
        if CONFIG.network_type == "development" and launch_rpc and not rpc.is_active():
            if is_connected():
                if web3.eth.block_number != 0:
                    warnings.warn(
                        f"Development network has a block height of {web3.eth.block_number}",
                        BrownieEnvironmentWarning,
                    )
                rpc.attach(host)
            else:
                rpc.launch(active["cmd"], **active["cmd_settings"])
        else:
            Accounts()._reset()
        if CONFIG.network_type == "live" or CONFIG.settings["dev_deployment_artifacts"]:
            for p in project.get_loaded_projects():
                p._load_deployments()

    except Exception:
        CONFIG.clear_active()
        web3.disconnect()
        raise


def disconnect(kill_rpc: bool = True) -> None:
    """Disconnects from the network."""
    if not is_connected():
        raise ConnectionError("Not connected to any network")
    CONFIG.clear_active()
    if kill_rpc and rpc.is_active():
        if rpc.is_child():
            rpc.kill()
    web3.disconnect()
    _notify_registry(0)


def show_active() -> Optional[str]:
    """Returns the name of the currently active network"""
    if not web3.provider:
        return None
    return CONFIG.active_network["id"]


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
            CONFIG.active_network["settings"]["gas_limit"] = False
        else:
            try:
                limit: int = int(args[0])  # type: ignore
            except ValueError:
                raise TypeError(f"Invalid gas limit '{args[0]}'")
            if limit < 21000:
                raise ValueError("Minimum gas limit is 21000")
            CONFIG.active_network["settings"]["gas_limit"] = limit
    return CONFIG.active_network["settings"]["gas_limit"]


def gas_price(*args: Tuple[Union[int, str, bool, None]]) -> Union[int, bool]:
    """Gets and optionally sets the default gas price.

    * If an integer value is given, this will be the default gas price.
    * If set to 'auto', the gas price is determined automatically."""

    if not is_connected():
        raise ConnectionError("Not connected to any network")
    if args:
        if isinstance(args[0], GasABC):
            CONFIG.active_network["settings"]["gas_price"] = args[0]
        elif args[0] in (None, False, True, "auto"):
            CONFIG.active_network["settings"]["gas_price"] = False
        else:
            try:
                price = Wei(args[0])
            except ValueError:
                raise TypeError(f"Invalid gas price '{args[0]}'")
            CONFIG.active_network["settings"]["gas_price"] = price
    return CONFIG.active_network["settings"]["gas_price"]


def gas_buffer(*args: Tuple[float, None]) -> Union[float, None]:
    if not is_connected():
        raise ConnectionError("Not connected to any network")
    if args:
        if args[0] is None:
            CONFIG.active_network["settings"]["gas_buffer"] = 1
        elif isinstance(args[0], (float, int)):
            CONFIG.active_network["settings"]["gas_buffer"] = args[0]
        else:
            raise TypeError("Invalid gas buffer - must be given as a float, int or None")
    return CONFIG.active_network["settings"]["gas_buffer"]


def max_fee(*args: Tuple[Union[int, str, bool, None]]) -> Union[int, bool]:
    """
    Gets and optionally sets the default max fee per gas.

    * If a Wei value is given, this will be the default max fee.
    * If set to None or False, transactions will default to using gas price.
    """
    if not is_connected():
        raise ConnectionError("Not connected to any network")
    if args:
        if args[0] in (None, False):
            CONFIG.active_network["settings"]["max_fee"] = None
        else:
            try:
                price = Wei(args[0])
            except ValueError:
                raise TypeError(f"Invalid max fee '{args[0]}'")
            CONFIG.active_network["settings"]["max_fee"] = price
    return CONFIG.active_network["settings"]["max_fee"]


def priority_fee(*args: Tuple[Union[int, str, bool, None]]) -> Union[int, bool]:
    """
    Gets and optionally sets the default max priority fee per gas.

    * If set to 'auto', the fee is set using `eth_maxPriorityFeePerGas`.
    * If a Wei value is given, this will be the default max fee.
    * If set to None or False, transactions will default to using gas price.
    """
    if not is_connected():
        raise ConnectionError("Not connected to any network")
    if args:
        if args[0] in (None, False):
            CONFIG.active_network["settings"]["priority_fee"] = None
        elif args[0] == "auto":
            CONFIG.active_network["settings"]["priority_fee"] = "auto"
        else:
            try:
                price = Wei(args[0])
            except ValueError:
                raise TypeError(f"Invalid priority fee '{args[0]}'")
            CONFIG.active_network["settings"]["priority_fee"] = price
    return CONFIG.active_network["settings"]["priority_fee"]
