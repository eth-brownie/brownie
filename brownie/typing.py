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
    linkReferences: NotRequired[Dict[str, Dict]]


@final
class DeployedBytecodeJson(BytecodeJson):
    sourceMap: str
    opcodes: str


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
    pcMap: Dict[int, "ProgramCounter"]
    compiler: NotRequired["CompilerConfig"]
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
EvmVersion = str
Source = Tuple[Start, Stop, ContractName, str]
StatementMap = Dict[str, Dict[int, Offset]]


class ContractSource(TypedDict):
    content: str


class InterfaceSource(TypedDict):
    abi: List[ABIElement]


SourcesDict = Dict[str, ContractSource | InterfaceSource]


@final
class OptimizerSettings(TypedDict):
    enabled: bool
    runs: int


@final
class SolcConfig(TypedDict):
    version: NotRequired[Optional[str]]
    evm_version: NotRequired[EvmVersion]
    optimize: NotRequired[bool]
    runs: NotRequired[int]
    remappings: NotRequired[List[str] | None]
    optimizer: NotRequired[OptimizerSettings]
    viaIR: NotRequired[bool]


@final
class VyperConfig(TypedDict):
    version: NotRequired[Optional[str]]
    evm_version: NotRequired[EvmVersion]


@final
class CompilerConfig(TypedDict):
    evm_version: EvmVersion | None
    solc: NotRequired[SolcConfig]
    vyper: VyperConfig
    version: NotRequired[str]
    optimizer: NotRequired[OptimizerSettings]


OutputSelection = Dict[str, Dict[str, List[str]]]


class _CompilerSettings(TypedDict):
    outputSelection: OutputSelection


@final
class SettingsSolc(_CompilerSettings):
    evmVersion: NotRequired[Optional[EvmVersion]]
    remappings: List[str]
    optimizer: NotRequired[OptimizerSettings]
    viaIR: NotRequired[bool]


@final
class SettingsVyper(_CompilerSettings):
    evmVersion: NotRequired[EvmVersion]


class _InputJsonBase(TypedDict):
    sources: SourcesDict

    # if I add a stub like this does it type check properly for members and fallbacks?
    def __getitem__(self, ContractName) -> Dict[str, Any]: ...  # type: ignore [misc]


@final
class InputJsonSolc(_InputJsonBase, total=False):
    language: Literal["Solidity", None]
    settings: SettingsSolc
    interfaces: Dict[str, InterfaceSource]


@final
class InputJsonVyper(_InputJsonBase, total=False):
    language: Literal["Vyper"]
    settings: SettingsVyper
    interfaces: Dict[str, InterfaceSource]


InputJson = InputJsonSolc | InputJsonVyper


Count = int


class ProgramCounter(TypedDict):
    count: Count
    fn: str
    op: str
    path: str
    value: str
    pc: NotRequired[int]
    branch: NotRequired[Count]
    jump: NotRequired[str]
    dev: NotRequired[str]
    offset: NotRequired[Offset]
    optimizer_revert: NotRequired[Literal[True]]
    first_revert: NotRequired[Literal[True]]
    jump_revert: NotRequired[Literal[True]]
    statement: NotRequired[Count]


PcList = List[ProgramCounter]


class VyperAstNode(TypedDict):
    """A dictionary representing on object on the AST."""

    name: str
    module: str
    type: str
    ast_type: str
    src: str
    op: "VyperAstNode"
    value: Dict
    test: Dict


VyperAstJson = List[VyperAstNode]
