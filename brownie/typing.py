from typing import TYPE_CHECKING, List, Literal, NewType, TypedDict, TypeVar, final

from eth_event.main import EventData
from eth_typing import ChecksumAddress

if TYPE_CHECKING:
    from brownie.network.account import Accounts
    from brownie.network.transaction import TransactionReceipt

# NETWORK
# Account
AccountsType = TypeVar("AccountsType", bound="Accounts")

# Contract
ContractName = NewType("ContractName", str)

# Event
@final
class FormattedEvent(TypedDict):
    name: str | Literal["(anonymous)", "(unknown)"]
    data: List[EventData]
    decoded: bool
    address: ChecksumAddress

# Transactions
TransactionReceiptType = TypeVar("TransactionReceiptType", bound="TransactionReceipt")
