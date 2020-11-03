#!/usr/bin/python3

"""
isort:skip_file
"""
from brownie.project import compile_source, run
from brownie._config import CONFIG as _CONFIG
from brownie.convert import Fixed, Wei
from brownie.network import accounts, alert, chain, history, rpc, web3
from brownie.network.contract import Contract  # NOQA: F401

ETH_ADDRESS = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

config = _CONFIG.settings

__all__ = [
    "Contract",
    "ETH_ADDRESS",
    "ZERO_ADDRESS",
    "accounts",  # accounts is an Accounts singleton
    "alert",
    "chain",
    "history",  # history is a TxHistory singleton
    "network",
    "rpc",  # rpc is a Rpc singleton
    "web3",  # web3 is a Web3 instance
    "project",
    "compile_source",
    "run",
    "Fixed",
    "Wei",
    "config",
]
