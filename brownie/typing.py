from typing import TYPE_CHECKING, List, Literal, TypedDict, TypeVar, final

from typing_extensions import NotRequired

from eth_event.main import EventData
from eth_typing import ChecksumAddress

if TYPE_CHECKING:
    from brownie.network.account import Accounts
    from brownie.network.transaction import TransactionReceipt

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
TransactionReceiptType = TypeVar("TransactionReceiptType", bound="TransactionReceipt")

# PROJECT
# Compiler
Language = str
EvmVersion = str

@final
class SolcConfig(TypedDict):
    version: NotRequired[str]
    evm_version: NotRequired[EvmVersion]
    optimize: NotRequired[bool]
    runs: NotRequired[int]
    remappings: NotRequired[List[dict]]
    optimizer: NotRequired[bool]
    viaIR: NotRequired[bool]

@final
class VyperConfig(TypedDict):
    version: NotRequired[str]
    evm_version: NotRequired[EvmVersion]

@final
class CompilerConfig(TypedDict):
    evm_version: EvmVersion
    solc_config: NotRequired[SolcConfig]
    vyper_config: VyperConfig

@final
class Settings(TypedDict):
    outputSelection: Dict[str, Dict[str, List[str]]]
    evmVersion: EvmVersion
    remappings: List[str]
    viaIR: NotRequired[bool]

@final
class InputJson(TypedDict):
    language: Optional[Language]
    sources: dict
    settings: Settings
