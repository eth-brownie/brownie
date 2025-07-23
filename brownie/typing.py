from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Literal,
    NewType,
    Optional,
    Tuple,
    TypedDict,
    TypeVar,
    final,
)

from eth_event.main import EventData
from eth_typing import ABIElement, ChecksumAddress, HexStr
from typing_extensions import NotRequired

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
Start = int
Stop = int
Offset = Tuple[Start, Stop]


# Build
class BytecodeJson(TypedDict):
    object: HexStr


@final
class DeployedBytecodeJson(BytecodeJson):
    opcodes: List[str]


class _BuildJsonBase(TypedDict):
    contractName: ContractName
    abi: List[ABIElement]
    sha1: HexStr
    dependencies: NotRequired[List[ContractName]]


@final
class InterfaceBuildJson(_BuildJsonBase):
    type: Literal["interface"]
    source: Optional[str]
    offset: Optional[Tuple[int, int]]
    ast: NotRequired[List[Dict]]


class _ContractBuildJson(_BuildJsonBase):
    source: str
    sourcePath: str
    natspec: NotRequired[Dict[str, Any]]
    allSourcePaths: Dict[str, Any]
    offset: Tuple[int, int]
    bytecode: HexStr
    bytecodeSha1: HexStr
    deployedBytecode: HexStr
    pcMap: Dict[int, Dict[str, Any]]
    compiler: NotRequired[Dict[str, Any]]  # TODO define typed dict
    ast: NotRequired[List]


@final
class SolidityBuildJson(_ContractBuildJson):
    type: str
    language: Literal["Solidity"]
    opcodes: NotRequired[List[str]]
    sourceMap: NotRequired[Dict]  # TODO: define typed dict
    deployedSourceMap: NotRequired[Dict]  # TODO: define typed dict
    coverageMap: Dict[str, Dict]  # TODO define typed dict


@final
class VyperBuildJson(_ContractBuildJson):
    type: Literal["contract"]
    language: Literal["Vyper"]


ContractBuildJson = SolidityBuildJson | VyperBuildJson
BuildJson = ContractBuildJson | InterfaceBuildJson


# Compiler
Language = Literal["Solidity", "Vyper"]
Source = Tuple[Start, Stop, ContractName, str]  # NewType("Source", Tuple[Start, Stop, ContractName, str])
