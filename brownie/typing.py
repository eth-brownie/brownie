from typing import TypeVar

from brownie.network.account import Accounts
from brownie.network.transaction import TransactionReceipt

# NETWORK
# Account
AccountsType = TypeVar("AccountsType", bound=Accounts)

# Transactions
TransactionReceiptType = TypeVar("TransactionReceiptType", bound=TransactionReceipt)
