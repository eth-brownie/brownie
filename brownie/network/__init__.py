#!/usr/bin/python3

from typing import Final

from brownie.network.account import accounts
# from brownie.network.account import Accounts
from brownie.network.main import (  # NOQA 401
    connect,
    disconnect,
    gas_limit,
    gas_price,
    is_connected,
    max_fee,
    priority_fee,
    show_active,
)
from brownie.network.rpc import Rpc
from brownie.network.state import Chain, TxHistory
from brownie.network.web3 import web3

# __all__ = ["accounts", "chain", "history", "rpc", "web3"]
__all__ = ["history", "rpc", "web3"]
__console_dir__ = ["connect", "disconnect", "show_active", "is_connected", "gas_limit", "gas_price"]

# accounts = Accounts()
rpc: Final[Rpc] = Rpc()
history: Final[TxHistory] = TxHistory()
# chain = Chain()
