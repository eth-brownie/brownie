from typing import TypeVar

# PROJECT

# NETWORK

# Transactions
from brownie.network.transaction import TransactionReceipt
TransactionReceiptType = TypeVar('TransactionReceiptType', bound=TransactionReceipt)

