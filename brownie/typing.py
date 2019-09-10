from typing import TypeVar
from brownie.network.transaction import TransactionReceipt

TransactionReceiptType = TypeVar('TransactionReceiptType', bound=TransactionReceipt)
