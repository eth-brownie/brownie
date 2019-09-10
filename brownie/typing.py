from typing import TypeVar

# PROJECT

# NETWORK

# Account
from brownie.network.account import Accounts
AccountsType = TypeVar('AccountsType', bound=Accounts)

# Transactions
from brownie.network.transaction import TransactionReceipt
TransactionReceiptType = TypeVar('TransactionReceiptType', bound=TransactionReceipt)

