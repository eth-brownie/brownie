from typing import List, Literal, TypedDict, TypeVar, final

from eth_event.main import EventData
from eth_typing import ChecksumAddress

from brownie.network.transaction import TransactionReceipt

if TYPE_CHECKING:
    from brownie.network.account import Accounts

# NETWORK
# Account
AccountsType = TypeVar("AccountsType", bound="Accounts")

# Event
@final
class FormattedEvent(TypedDict):
    name: str | Literal["(anonymous)", "(unknown)"]
    data: List[EventData]
    decoded: bool
    address: ChecksumAddress

# Transactions
TransactionReceiptType = TypeVar("TransactionReceiptType", bound=TransactionReceipt)
