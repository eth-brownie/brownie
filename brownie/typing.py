from typing import TYPE_CHECKING, Any, Literal, NewType, TypedDict, TypeVar, final

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
FunctionName = NewType("FunctionName", str)
Selector = NewType("Selector", HexStr)


# Event
@final
class FormattedEvent(TypedDict):
    name: str | Literal["(anonymous)", "(unknown)"]
    data: list[EventData]
    decoded: bool
    address: ChecksumAddress


# Transactions
TransactionReceiptType = TypeVar("TransactionReceiptType", bound="TransactionReceipt")


# PROJECT
Start = int
Stop = int
Offset = tuple[Start, Stop]


# Build
class BytecodeJson(TypedDict):
    object: HexStr
    linkReferences: NotRequired[dict[str, dict]]


@final
class DeployedBytecodeJson(BytecodeJson):
    sourceMap: str
    opcodes: str


class _BuildJsonBase(TypedDict):
    contractName: ContractName
    abi: list[ABIElement]
    sha1: HexStr
    dependencies: NotRequired[list[ContractName]]


@final
class InterfaceBuildJson(_BuildJsonBase):
    type: Literal["interface"]
    source: str | None
    offset: Offset | None
    ast: NotRequired[list[dict]]


IntegerString = str
"""An integer cast as a string, as in: ``str(123)``"""

Statements = dict[str, dict["Count", Offset]]
StatementMap = dict[IntegerString, Statements]

Branches = dict[str, dict["Count", tuple[int, int, bool]]]
BranchMap = dict[IntegerString, Branches]


class CoverageMap(TypedDict):
    statements: StatementMap
    branches: BranchMap


class _ContractBuildJson(_BuildJsonBase):
    source: str
    sourcePath: str
    natspec: NotRequired[dict[str, Any]]
    allSourcePaths: dict[str, Any]
    offset: Offset
    bytecode: HexStr
    bytecodeSha1: HexStr
    deployedBytecode: HexStr
    coverageMap: CoverageMap
    pcMap: dict[int, "ProgramCounter"]
    compiler: NotRequired["CompilerConfig"]
    ast: NotRequired[list]


@final
class SolidityBuildJson(_ContractBuildJson):
    type: str
    language: Literal["Solidity"]
    opcodes: NotRequired[list[str]]
    sourceMap: NotRequired[dict]  # TODO: define typed dict
    deployedSourceMap: NotRequired[dict]  # TODO: define typed dict


@final
class VyperBuildJson(_ContractBuildJson):
    type: Literal["contract"]
    language: Literal["Vyper"]


ContractBuildJson = SolidityBuildJson | VyperBuildJson
BuildJson = ContractBuildJson | InterfaceBuildJson


# Compiler
Language = Literal["Solidity", "Vyper"]
EvmVersion = NewType("EvmVersion", str)
ContractId = NewType("ContractId", int)
JumpCode = NewType("JumpCode", int)
Source = tuple[Start, Stop, ContractId | Literal[-1], JumpCode]


class ContractSource(TypedDict):
    content: str


class InterfaceSource(TypedDict):
    abi: list[ABIElement]


SourcesDict = dict[str, ContractSource | InterfaceSource]
InterfaceSources = dict[str, InterfaceSource]


@final
class OptimizerSettings(TypedDict):
    enabled: bool
    runs: int


@final
class SolcConfig(TypedDict):
    version: NotRequired[str | None]
    evm_version: NotRequired[EvmVersion]
    optimize: NotRequired[bool]
    runs: NotRequired[int]
    remappings: NotRequired[list[str] | None]
    optimizer: NotRequired[OptimizerSettings]
    viaIR: NotRequired[bool]


@final
class VyperConfig(TypedDict):
    version: NotRequired[str | None]
    evm_version: NotRequired[EvmVersion]


@final
class CompilerConfig(TypedDict):
    evm_version: EvmVersion | None
    solc: NotRequired[SolcConfig]
    vyper: VyperConfig
    version: NotRequired[str]
    optimizer: NotRequired[OptimizerSettings]


OutputSelection = dict[str, dict[str, list[str]]]


class _CompilerSettings(TypedDict):
    outputSelection: OutputSelection


@final
class SettingsSolc(_CompilerSettings):
    evmVersion: NotRequired[EvmVersion | None]
    remappings: list[str]
    optimizer: NotRequired[OptimizerSettings]
    viaIR: NotRequired[bool]


@final
class SettingsVyper(_CompilerSettings):
    evmVersion: NotRequired[EvmVersion]


class _InputJsonBase(TypedDict):
    sources: SourcesDict  # NOTE: should this be contract sources?
    interfaces: InterfaceSources

    # if I add a stub like this does it type check properly for members and fallbacks?
    def __getitem__(self, name: ContractName) -> dict[str, Any]: ...  # type: ignore [misc]


@final
class InputJsonSolc(_InputJsonBase, total=False):
    language: Literal["Solidity", None]
    settings: SettingsSolc


@final
class InputJsonVyper(_InputJsonBase, total=False):
    language: Literal["Vyper"]
    settings: SettingsVyper


InputJson = InputJsonSolc | InputJsonVyper


Count = int


class ProgramCounter(TypedDict):
    count: Count
    op: str
    fn: NotRequired[str | None]
    path: NotRequired[str]
    value: NotRequired[str]
    pc: NotRequired[int]
    branch: NotRequired[Count]
    jump: NotRequired[str]
    dev: NotRequired[str]
    offset: NotRequired[Offset]
    optimizer_revert: NotRequired[Literal[True]]
    first_revert: NotRequired[Literal[True]]
    jump_revert: NotRequired[Literal[True]]
    statement: NotRequired[Count]


PcList = list[ProgramCounter]
PCMap = NewType("PCMap", dict[int, ProgramCounter])


class VyperAstNode(TypedDict):
    """A dictionary representing on object on the AST."""

    name: str
    module: str
    type: str
    ast_type: str
    src: str
    op: "VyperAstNode"
    value: dict
    test: dict


VyperAstJson = list[VyperAstNode]
