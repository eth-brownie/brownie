#!/usr/bin/python3

from typing import Final

from .account import Accounts
from .main import (  # NOQA 401
    connect,
    disconnect,
    gas_limit,
    gas_price,
    is_connected,
    max_fee,
    priority_fee,
    show_active,
)
from .rpc import rpc
from .state import Chain, TxHistory
from .web3 import web3

__all__ = ["accounts", "chain", "history", "rpc", "web3"]
__console_dir__ = ["connect", "disconnect", "show_active", "is_connected", "gas_limit", "gas_price"]

accounts: Final[Accounts] = Accounts()
history: Final[TxHistory] = TxHistory()
chain: Final[Chain] = Chain()
