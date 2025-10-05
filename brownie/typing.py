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
from eth_typing import ABIConstructor as _ABIConstructor
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


class ABIConstructorWithName(_ABIConstructor):
    name: Literal["constructor"]


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
    offset: Optional[Offset]
    ast: NotRequired[List[Dict]]


IntegerString = str
"""An integer cast as a string, as in: ``str(123)``"""

Statements = Dict[str, Dict["Count", Offset]]
StatementMap = Dict[IntegerString, Statements]

Branches = Dict[str, Dict["Count", Tuple[int, int, bool]]]
BranchMap = Dict[IntegerString, Branches]


class CoverageMap(TypedDict):
    statements: StatementMap
    branches: BranchMap


class _ContractBuildJson(_BuildJsonBase):
    source: str
    sourcePath: str
    natspec: NotRequired[Dict[str, Any]]
    allSourcePaths: Dict[str, Any]
    offset: Offset
    bytecode: HexStr
    bytecodeSha1: HexStr
    deployedBytecode: HexStr
    coverageMap: CoverageMap
    pcMap: NotRequired[Dict[int, "ProgramCounter"]]
    compiler: NotRequired["CompilerConfig"]
    ast: NotRequired[List]


class SolidityBuildJson(_ContractBuildJson):
    type: str
    language: Literal["Solidity"]
    opcodes: NotRequired[List[str]]
    sourceMap: NotRequired[Dict]  # TODO: define typed dict
    deployedSourceMap: NotRequired[Dict]  # TODO: define typed dict


class VyperBuildJson(_ContractBuildJson):
    type: Literal["contract"]
    language: Literal["Vyper"]


ContractBuildJson = SolidityBuildJson | VyperBuildJson
BuildJson = ContractBuildJson | InterfaceBuildJson


@final
class SolidityDeploymentJson(SolidityBuildJson):
    address: ChecksumAddress
    alias: NotRequired[ContractName]


@final
class VyperDeploymentJson(VyperBuildJson):
    address: ChecksumAddress
    alias: NotRequired[ContractName]


ContractDeploymentJson = SolidityDeploymentJson | VyperDeploymentJson


# Compiler
Language = Literal["Solidity", "Vyper"]
EvmVersion = str
Source = Tuple[Start, Stop, ContractName, str]


class ContractSource(TypedDict):
    content: str


class InterfaceSource(TypedDict):
    abi: List[ABIElement]


SourcesDict = Dict[str, ContractSource | InterfaceSource]
InterfaceSources = Dict[str, InterfaceSource]


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
    sources: SourcesDict  # NOTE: should this be contract sources?
    interfaces: InterfaceSources

    # if I add a stub like this does it type check properly for members and fallbacks?
    def __getitem__(self, name: ContractName) -> Dict[str, Any]: ...  # type: ignore [misc]


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
    fn: NotRequired[Optional[str]]
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
