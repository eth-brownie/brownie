from typing import (
    TYPE_CHECKING,
    List,
    Literal,
    NewType,
    Tuple,
    TypedDict,
    TypeVar,
    final,
)

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

# PROJECT
Start = int  # NewType("Start", int)
Stop = int  # NewType("Stop", int)
Offset = Tuple[Start, Stop]  # NewType("Offset", Tuple[Start, Stop])

# Compiler
Language = Literal["Solidity", "Vyper"]
Source = Tuple[Start, Stop, ContractName, str]  # NewType("Source", Tuple[Start, Stop, ContractName, str])
