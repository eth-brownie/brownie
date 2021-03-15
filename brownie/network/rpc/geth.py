#!/usr/bin/python3

import sys
from subprocess import DEVNULL, PIPE
from typing import Dict, List, Optional

import psutil
from requests.exceptions import ConnectionError as RequestsConnectionError

from brownie.exceptions import RPCRequestError
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
    print(f"\nLaunching '{cmd}'...")
    out = DEVNULL if sys.platform == "win32" else PIPE

    return psutil.Popen([cmd], stdin=DEVNULL, stdout=out, stderr=out)


def _request(method: str, args: List) -> int:
    try:
        response = web3.provider.make_request(method, args)  # type: ignore
        if "result" in response:
            return response["result"]
    except (AttributeError, RequestsConnectionError):
        raise RPCRequestError("Web3 is not connected.")
    raise RPCRequestError(response["error"]["message"])


def sleep(seconds: int) -> None:
    raise NotImplementedError("Geth dev does not support time travel")


def mine(timestamp: Optional[int] = None) -> None:
    params = [timestamp] if timestamp else []
    _request("evm_mine", params)


def snapshot() -> int:
    return web3.eth.blockNumber


def revert(snapshot_id):
    _request("debug_setHead", [hex(snapshot_id)])
