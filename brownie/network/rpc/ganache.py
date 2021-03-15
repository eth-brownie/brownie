#!/usr/bin/python3

import datetime
import sys
import warnings
from subprocess import DEVNULL, PIPE
from typing import Dict, List, Optional

import psutil
from hexbytes import HexBytes
from requests.exceptions import ConnectionError as RequestsConnectionError

from brownie._config import EVM_EQUIVALENTS
from brownie.convert import Wei
from brownie.exceptions import InvalidArgumentWarning, RPCRequestError
from brownie.network.web3 import web3

CLI_FLAGS = {
    "port": "--port",
    "gas_limit": "--gasLimit",
    "accounts": "--accounts",
    "evm_version": "--hardfork",
    "fork": "--fork",
    "mnemonic": "--mnemonic",
    "account_keys_path": "--acctKeys",
    "block_time": "--blockTime",
    "default_balance": "--defaultBalanceEther",
    "time": "--time",
    "unlock": "--unlock",
    "network_id": "--networkId",
    "chain_id": "--chainId",
}

EVM_VERSIONS = ["byzantium", "constantinople", "petersburg", "istanbul"]
EVM_DEFAULT = "istanbul"


def launch(cmd: str, **kwargs: Dict) -> None:
    """Launches the RPC client.

    Args:
        cmd: command string to execute as subprocess"""
    if sys.platform == "win32" and not cmd.split(" ")[0].endswith(".cmd"):
        if " " in cmd:
            cmd = cmd.replace(" ", ".cmd ", 1)
        else:
            cmd += ".cmd"
    cmd_list = cmd.split(" ")
    kwargs.setdefault("evm_version", EVM_DEFAULT)  # type: ignore
    if kwargs["evm_version"] in EVM_EQUIVALENTS:
        kwargs["evm_version"] = EVM_EQUIVALENTS[kwargs["evm_version"]]  # type: ignore
    kwargs = _validate_cmd_settings(kwargs)
    for key, value in [(k, v) for k, v in kwargs.items() if v]:
        if key == "unlock":
            if not isinstance(value, list):
                value = [value]  # type: ignore
            for address in value:
                if isinstance(address, int):
                    address = HexBytes(address.to_bytes(20, "big")).hex()
                cmd_list.extend([CLI_FLAGS[key], address])
        else:
            try:
                cmd_list.extend([CLI_FLAGS[key], str(value)])
            except KeyError:
                warnings.warn(
                    f"Ignoring invalid commandline setting for ganache-cli: "
                    f'"{key}" with value "{value}".',
                    InvalidArgumentWarning,
                )
    print(f"\nLaunching '{' '.join(cmd_list)}'...")
    out = DEVNULL if sys.platform == "win32" else PIPE

    return psutil.Popen(cmd_list, stdin=DEVNULL, stdout=out, stderr=out)


def on_connection() -> None:
    pass


def _request(method: str, args: List) -> int:
    try:
        response = web3.provider.make_request(method, args)  # type: ignore
        if "result" in response:
            return response["result"]
    except (AttributeError, RequestsConnectionError):
        raise RPCRequestError("Web3 is not connected.")
    raise RPCRequestError(response["error"]["message"])


def sleep(seconds: int) -> int:
    return _request("evm_increaseTime", [seconds])


def mine(timestamp: Optional[int] = None) -> None:
    params = [timestamp] if timestamp else []
    _request("evm_mine", params)


def snapshot() -> int:
    return _request("evm_snapshot", [])


def revert(snapshot_id: int) -> None:
    _request("evm_revert", [snapshot_id])


def unlock_account(address: str) -> None:
    web3.provider.make_request("evm_unlockUnknownAccount", [address])  # type: ignore


def _validate_cmd_settings(cmd_settings: dict) -> dict:
    CMD_TYPES = {
        "port": int,
        "gas_limit": int,
        "block_time": int,
        "time": datetime.datetime,
        "accounts": int,
        "evm_version": str,
        "mnemonic": str,
        "account_keys_path": str,
        "fork": str,
        "network_id": int,
        "chain_id": int,
    }
    for cmd, value in cmd_settings.items():
        if (
            cmd in CLI_FLAGS.keys()
            and cmd in CMD_TYPES.keys()
            and not isinstance(value, CMD_TYPES[cmd])
        ):
            raise TypeError(
                f'Wrong type for cmd_settings "{cmd}": {value}. '
                f"Found {type(value).__name__}, but expected {CMD_TYPES[cmd].__name__}."
            )

    if "default_balance" in cmd_settings:
        try:
            cmd_settings["default_balance"] = int(cmd_settings["default_balance"])
        except ValueError:
            # convert any input to ether, then format it properly
            default_eth = Wei(cmd_settings["default_balance"]).to("ether")
            cmd_settings["default_balance"] = (
                default_eth.quantize(1) if default_eth > 1 else default_eth.normalize()
            )
    return cmd_settings
