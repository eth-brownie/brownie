#!/usr/bin/python3

import asyncio
import io
import os
import random
import time
import warnings
from collections.abc import Callable, Coroutine, Iterator
from pathlib import Path
from re import Match
from textwrap import TextWrapper
from threading import get_ident  # noqa
from typing import TYPE_CHECKING, Any, Final, Optional, Union

import requests
import solcx
from eth_typing import ABIConstructor, ABIElement, ABIFunction, ChecksumAddress, HexAddress, HexStr
from faster_eth_abi import decode as decode_abi
from faster_eth_abi import encode as encode_abi
from faster_eth_utils import combomethod
from vvm import get_installable_vyper_versions
from vvm.utils.convert import to_vyper_version
from web3._utils import filters
from web3.datastructures import AttributeDict
from web3.types import LogReceipt

from brownie._c_constants import (
    HexBytes,
    Version,
    regex_findall,
    ujson_dump,
    ujson_dumps,
    ujson_load,
    ujson_loads,
)
from brownie._config import BROWNIE_FOLDER, CONFIG, REQUEST_HEADERS, _load_project_compiler_config
from brownie.convert.datatypes import Wei
from brownie.convert.normalize import format_input, format_output
from brownie.convert.utils import (
    build_function_selector,
    build_function_signature,
    get_type_strings,
)
from brownie.exceptions import (
    BrownieCompilerWarning,
    BrownieEnvironmentWarning,
    ContractExists,
    ContractNotFound,
    UndeployedLibrary,
    VirtualMachineError,
    decode_typed_error,
    parse_errors_from_abi,
)
from brownie.project import compiler
from brownie.project.flattener import Flattener
from brownie.typing import (
    AccountsType,
    ContractBuildJson,
    ContractName,
    FunctionName,
    Language,
    Selector,
    TransactionReceiptType,
)
from brownie.utils import color, hexbytes_to_hexstring
from brownie.utils._color import bright_blue, bright_green, bright_magenta, bright_red

from brownie.network.account import accounts
from brownie.network.event import _add_deployment_topics, _get_topics, event_watcher
from brownie.network.state import (
    chain,
    _add_contract,
    _add_deployment,
    _find_contract,
    _get_deployment,
    _remove_contract,
    _remove_deployment,
    _revert_register,
)
from brownie.network.web3 import ContractEvent, _ContractEvents, _resolve_address, web3

if TYPE_CHECKING:
    from brownie.project.main import Project, TempProject

AnyContractMethod = Union["ContractCall", "ContractTx", "OverloadedMethod"]

_unverified_addresses: Final[set[ChecksumAddress]] = set()

_explorer_tokens = {
    "optimistic": "OPTIMISMSCAN_TOKEN",
    "etherscan": "ETHERSCAN_TOKEN",
    "bscscan": "BSCSCAN_TOKEN",
    "zkevm": "ZKEVMSCAN_TOKEN",
    "polygonscan": "POLYGONSCAN_TOKEN",
    "ftmscan": "FTMSCAN_TOKEN",
    "arbiscan": "ARBISCAN_TOKEN",
    "snowtrace": "SNOWTRACE_TOKEN",
    "snowscan": "SNOWTRACE_TOKEN",
    "aurorascan": "AURORASCAN_TOKEN",
    "moonscan": "MOONSCAN_TOKEN",
    "gnosisscan": "GNOSISSCAN_TOKEN",
    "base": "BASESCAN_TOKEN",
    "blastscan": "BLASTSCAN_TOKEN",
    "zksync": "ZKSYNCSCAN_TOKEN",
}

_rng = random.Random()

class _ContractBase:
    _dir_color: Final = "bright magenta"

    def __init__(
        self,
        project: Union["Project", "TempProject"] | None,
        build: ContractBuildJson,
        sources: dict[str, Any],
    ) -> None:
        self._project = project
        self._build: Final = build.copy()
        self._sources: Final = sources

        abi = self.abi
        self.topics: Final = _get_topics(abi)
        self.selectors: Final[dict[Selector, FunctionName]] = {
            build_function_selector(i): f"{i['type']} {build_function_signature(i)}"
            for i in abi
            if i["type"] in ("function", "error", "event")
        }
        # JPD fixed: this isn't fully accurate because of overloaded methods - will be removed in `v2.0.0`
        self.signatures: Final[dict[FunctionName, Selector]] = {
            build_function_signature(i): build_function_selector(i)
            for i in self.abi
            if i["type"] in ("function", "error", "event")
        }
        parse_errors_from_abi(abi)

    @property
    def abi(self) -> list[ABIElement]:
        return self._build["abi"]

    @property
    def _name(self) -> ContractName:
        return self._build["contractName"]

    def info(self) -> None:
        """
        Display NatSpec documentation for this contract.
        """
        if natspec := self._build.get("natspec"):
            _print_natspec(natspec)

    def get_method(self, calldata: str) -> str | None:
        sig = calldata[:10].lower()
        return self.selectors.get(sig)

    def decode_input(self, calldata: str | bytes) -> tuple[str, Any]:
        """
        Decode input calldata for this contract.

        Arguments
        ---------
        calldata : str | bytes
            Calldata for a call to this contract

        Returns
        -------
        str
            Signature of the function that was called
        Any
            Decoded input arguments
        """
        if not isinstance(calldata, HexBytes):
            calldata = HexBytes(calldata)

        fn_selector = hexbytes_to_hexstring(calldata[:4])

        abi: ABIFunction | None = None
        for i in self.abi:
            if i["type"] in ("function", "error", "event") and build_function_selector(i) == fn_selector:
                abi = i
                break

        if abi is None:
            if fn_selector == "0x08c379a0":
                abi = {
                    "inputs": [{"name": "message", "type": "string"}],
                    "name": "Error",
                    "type": "error",
                }
            else:
                raise ValueError("Four byte selector does not match the ABI for this contract")

        function_sig = build_function_signature(abi)

        types_list = get_type_strings(abi["inputs"])
        result = decode_abi(types_list, calldata[4:])
        input_args = format_input(abi, result)

        return function_sig, input_args


class ContractContainer(_ContractBase):
    """List-like container class that holds all Contract instances of the same
    type, and is used to deploy new instances of that contract.

    Attributes:
        abi: Complete contract ABI.
        bytecode: Bytecode used to deploy the contract.
        signatures: Dictionary of {'function name': "bytes4 signature"}
        topics: Dictionary of {'event name': "bytes32 topic"}"""

    def __init__(self, project: Any, build: ContractBuildJson) -> None:
        self.tx = None
        self.bytecode: Final = build["bytecode"]
        self._contracts: Final[list["ProjectContract"]] = []
        super().__init__(project, build, project._sources)
        self.deploy: Final = ContractConstructor(self, self._name)
        _revert_register(self)

        # messes with tests if it is created on init
        # instead we create when it's requested, but still define it here
        self._flattener: Flattener = None

    def __iter__(self) -> Iterator["ProjectContract"]:
        return iter(self._contracts)

    def __getitem__(self, i: Any) -> "ProjectContract":
        return self._contracts[i]

    def __delitem__(self, key: Any) -> None:
        item = self._contracts[key]
        self.remove(item)

    def __len__(self) -> int:
        return len(self._contracts)

    def __repr__(self) -> str:
        if CONFIG.argv["cli"] == "console":
            return str(self._contracts)
        return super().__repr__()

    def _reset(self) -> None:
        for contract in self._contracts:
            _remove_contract(contract)
            contract._reverted = True
        self._contracts.clear()

    def _revert(self, height: int) -> None:
        reverted = [
            i
            for i in self._contracts
            if (i.tx and i.tx.block_number is not None and i.tx.block_number > height)
            # removeprefix is used for compatibility with both hexbytes<1 and >=1
            or len(web3.eth.get_code(i.address).hex().removeprefix("0x")) <= 2
        ]
        for contract in reverted:
            self.remove(contract)
            contract._reverted = True

    def remove(self, contract: "ProjectContract") -> None:
        """Removes a contract from the container.

        Args:
            contract: Contract instance of address string of the contract."""
        if contract not in self._contracts:
            raise TypeError("Object is not in container.")
        self._contracts.remove(contract)
        contract._delete_deployment()
        _remove_contract(contract)

    def at(
        self,
        address: HexAddress,
        owner: AccountsType | None = None,
        tx: TransactionReceiptType | None = None,
        persist: bool = True,
    ) -> "ProjectContract":
        """Returns a contract address.

        Raises ValueError if no bytecode exists at the address.

        Args:
            address: Address string of the contract.
            owner: Default Account instance to send contract transactions from.
            tx: Transaction ID of the contract creation."""
        address = _resolve_address(address)
        contract = _find_contract(address)
        if isinstance(contract, ProjectContract):
            if contract._name == self._name and contract._project == self._project:
                return contract
            raise ContractExists(
                f"'{contract._name}' declared at {address} in project '{contract._project._name}'"
            )

        build = self._build
        contract = ProjectContract(self._project, build, address, owner, tx)
        if not _verify_deployed_code(address, build["deployedBytecode"], build["language"]):
            # prevent trace attempts when the bytecode doesn't match
            del contract._build["pcMap"]

        contract._save_deployment()
        _add_contract(contract)
        self._contracts.append(contract)
        if CONFIG.network_type == "live" and persist:
            _add_deployment(contract)

        return contract

    def _add_from_tx(self, tx: TransactionReceiptType) -> None:
        tx._confirmed.wait()
        if tx.status and tx.contract_address is not None:
            try:
                self.at(tx.contract_address, tx.sender, tx)
            except ContractNotFound:
                # if the contract self-destructed during deployment
                pass

    def get_verification_info(self) -> dict:
        """
        Return a dict with flattened source code for this contract
        and further information needed for verification
        """
        language = self._build["language"]
        if language == "Vyper":
            raise TypeError(
                "Etherscan does not support API verification of source code "
                "for vyper contracts. You need to verify the source manually"
            )
        elif language == "Solidity":
            if self._flattener is None:
                source_fp = (
                    Path(self._project._path)
                    .joinpath(self._build["sourcePath"])
                    .resolve()
                    .as_posix()
                )
                config = self._project._compiler_config
                remaps = dict(
                    map(
                        lambda s: s.split("=", 1),
                        compiler._get_solc_remappings(config["solc"]["remappings"]),
                    )
                )
                libs = {lib.strip("_") for lib in regex_findall("_{1,}[^_]*_{1,}", self.bytecode)}
                compiler_settings = {
                    "evmVersion": self._build["compiler"]["evm_version"],
                    "optimizer": config["solc"]["optimizer"],
                    "libraries": {
                        Path(source_fp).name: {lib: self._project[lib][-1].address for lib in libs}
                    },
                }
                self._flattener = Flattener(source_fp, self._name, remaps, compiler_settings)

            build_json = self._build

            return {
                "standard_json_input": self._flattener.standard_input_json,
                "contract_name": build_json["contractName"],
                "compiler_version": build_json["compiler"]["version"],
                "optimizer_enabled": build_json["compiler"]["optimizer"]["enabled"],
                "optimizer_runs": build_json["compiler"]["optimizer"]["runs"],
                "license_identifier": self._flattener.license,
                "bytecode_len": len(build_json["bytecode"]),
            }
        else:
            raise TypeError(f"Unsupported language for source verification: {language}")

    def publish_source(self, contract: "Contract", silent: bool = False) -> bool:
        """Flatten contract and publish source on the selected explorer"""

        api_key = os.getenv("ETHERSCAN_TOKEN")
        if api_key is None:
            raise ValueError(
                "An API token is required to verify contract source code. "
                "Visit https://etherscan.io/register to obtain a token, and "
                "then store it as the environment variable $ETHERSCAN_TOKEN"
            )

        address = _resolve_address(contract.address)

        # Get source code and contract/compiler information
        contract_info = self.get_verification_info()

        # Select matching license code (https://etherscan.io/contract-license-types)
        license_code = 1
        identifier = contract_info["license_identifier"].lower()
        if "unlicensed" in identifier:
            license_code = 2
        elif "mit" in identifier:
            license_code = 3
        elif "agpl" in identifier and "3.0" in identifier:
            license_code = 13
        elif "lgpl" in identifier:
            if "2.1" in identifier:
                license_code = 6
            elif "3.0" in identifier:
                license_code = 7
        elif "gpl" in identifier:
            if "2.0" in identifier:
                license_code = 4
            elif "3.0" in identifier:
                license_code = 5
        elif "bsd-2-clause" in identifier:
            license_code = 8
        elif "bsd-3-clause" in identifier:
            license_code = 9
        elif "mpl" in identifier and "2.0" in identifier:
            license_code = 10
        elif identifier.startswith("osl") and "3.0" in identifier:
            license_code = 11
        elif "apache" in identifier and "2.0" in identifier:
            license_code = 12

        # get constructor arguments
        url = "https://api.etherscan.io/v2/api"
        params_tx: dict = {
            "chainid": web3.chain_id,
            "apikey": api_key,
            "module": "account",
            "action": "txlist",
            "address": address,
            "page": 1,
            "sort": "asc",
            "offset": 1,
        }
        i = 0
        while True:
            response = requests.get(url, params=params_tx, headers=REQUEST_HEADERS)
            if response.status_code != 200:
                raise ConnectionError(
                    f"Status {response.status_code} when querying {url}: {response.text}"
                )
            data = response.json()
            if int(data["status"]) == 1:
                # Constructor arguments received
                break

            # Wait for contract to be recognized by etherscan
            # This takes a few seconds after the contract is deployed
            # After 10 loops we throw with the API result message (includes address)
            if i >= 10:
                raise ValueError(f"API request failed with: {data['result']}")
            elif i == 0 and not silent:
                print(f"Waiting for {url} to process contract...")
            i += 1
            time.sleep(10)

        if data["message"] == "OK":
            constructor_arguments = data["result"][0]["input"][contract_info["bytecode_len"] + 2 :]
        else:
            constructor_arguments = ""

        # Submit verification
        payload_verification: dict = {
            "apikey": api_key,
            "module": "contract",
            "action": "verifysourcecode",
            "contractaddress": address,
            "sourceCode": io.StringIO(ujson_dumps(self._flattener.standard_input_json)),
            "codeformat": "solidity-standard-json-input",
            "contractname": f"{self._flattener.contract_file}:{self._flattener.contract_name}",
            "compilerversion": f"v{contract_info['compiler_version']}",
            "optimizationUsed": 1 if contract_info["optimizer_enabled"] else 0,
            "runs": contract_info["optimizer_runs"],
            # NOTE: This typo is intentional.
            # https://docs.etherscan.io/etherscan-v2/common-verification-errors
            # "There is an easter egg 🐣 on the constructorArguements field spelling,
            # using it as the "correct" spelling may miss your submission!"
            "constructorArguements": constructor_arguments,
            "licenseType": license_code,
        }
        response = requests.post(
            f"{url}?chainid={web3.chain_id}", data=payload_verification, headers=REQUEST_HEADERS
        )
        if response.status_code != 200:
            raise ConnectionError(
                f"Status {response.status_code} when querying {url}: {response.text}"
            )
        data = response.json()
        if int(data["status"]) != 1:
            raise ValueError(f"Failed to submit verification request: {data['result']}")

        # Status of request
        guid = data["result"]
        if not silent:
            print("Verification submitted successfully. Waiting for result...")
        time.sleep(10)
        params_status: dict = {
            "chainid": web3.chain_id,
            "apikey": api_key,
            "module": "contract",
            "action": "checkverifystatus",
            "guid": guid,
        }
        while True:
            response = requests.get(url, params=params_status, headers=REQUEST_HEADERS)
            if response.status_code != 200:
                raise ConnectionError(
                    f"Status {response.status_code} when querying {url}: {response.text}"
                )
            data = response.json()
            if data["result"] == "Pending in queue":
                if not silent:
                    print("Verification pending...")
            else:
                success = (data["message"] == "OK" or data["message"] == "Already Verified")
                if not silent:
                    color = bright_green if success else bright_red
                    print(f"Verification complete. Result: {color}{data['result']}{color}")
                return success
            time.sleep(10)

    def _slice_source(self, source: str, offset: list) -> str:
        """Slice the source of the contract, preserving any comments above the first line."""
        offset_start = offset[0]
        top_source = source[:offset_start]
        top_lines = top_source.split("\n")[::-1]
        comment_open = False
        for line in top_lines:
            stripped = line.strip()
            if (
                not stripped
                or stripped.startswith(("//", "/*", "*"))
                or stripped.endswith("*/")
                or comment_open
            ):
                offset_start = offset_start - len(line) - 1
                if stripped.endswith("*/"):
                    comment_open = True
                elif stripped.startswith("/*"):
                    comment_open = False
            else:
                # Stop on the first non-empty, non-comment line
                break
        offset_start = max(0, offset_start)
        return source[offset_start : offset[1]].strip()


class ContractConstructor:
    _dir_color: Final = "bright magenta"

    def __init__(self, parent: "ContractContainer", name: ContractName) -> None:
        self._parent: Final = parent
        try:
            abi = next(i for i in parent.abi if i["type"] == "constructor")
        except Exception:
            abi: ABIConstructor = {"inputs": [], "name": "constructor", "type": "constructor"}
        else:
            abi["name"] = "constructor"
        self.abi: Final = abi
        self._name: Final = name

    @property
    def payable(self) -> bool:
        abi = self.abi
        if "payable" in abi:
            return abi["payable"]
        else:
            return abi["stateMutability"] == "payable"

    def __repr__(self) -> str:
        return f"<{type(self).__name__} '{self._name}.constructor({_inputs(self.abi)})'>"

    def __call__(
        self, *args: Any, publish_source: bool = False, silent: bool = False
    ) -> Union["Contract", TransactionReceiptType]:
        """Deploys a contract.

        Args:
            *args: Constructor arguments. The last argument MUST be a dictionary
                   of transaction values containing at minimum a 'from' key to
                   specify which account to deploy this contract from.

        Returns:
            * Contract instance if the transaction confirms
            * TransactionReceipt if the transaction is pending or reverts"""
        args, tx = _get_tx(None, args)
        if not tx["from"]:
            raise AttributeError(
                "Final argument must be a dict of transaction parameters that "
                "includes a `from` field specifying the address to deploy from"
            )

        return tx["from"].deploy(
            self._parent,
            *args,
            amount=tx["value"],
            gas_limit=tx["gas"],
            gas_price=tx.get("gas_price"),
            max_fee=tx.get("max_fee"),
            priority_fee=tx.get("priority_fee"),
            nonce=tx["nonce"],
            required_confs=tx["required_confs"],
            allow_revert=tx.get("allow_revert"),
            publish_source=publish_source,
            silent=silent,
        )

    @staticmethod
    def _autosuggest(obj: "ContractConstructor") -> list[str]:
        return _contract_method_autosuggest(obj.abi["inputs"], True, obj.payable)

    def encode_input(self, *args: Any) -> str:
        bytecode = self._parent.bytecode
        # find and replace unlinked library pointers in bytecode
        for marker in regex_findall("_{1,}[^_]*_{1,}", bytecode):
            library = marker.strip("_")
            if not self._parent._project[library]:
                raise UndeployedLibrary(
                    f"Contract requires '{library}' library, but it has not been deployed yet"
                )
            address = self._parent._project[library][-1].address[-40:]
            bytecode = bytecode.replace(marker, address)

        abi = self.abi
        data = format_input(abi, args)
        types_list = get_type_strings(abi["inputs"])
        return bytecode + encode_abi(types_list, data).hex()

    def estimate_gas(self, *args: Any) -> int:
        """
        Estimate the gas cost for the deployment.

        Raises VirtualMachineError if the transaction would revert.

        Arguments
        ---------
        *args
            Constructor arguments. The last argument MUST be a dictionary
            of transaction values containing at minimum a 'from' key to
            specify which account to deploy this contract from.

        Returns
        -------
        int
            Estimated gas value in wei.
        """
        args, tx = _get_tx(None, args)
        if not tx["from"]:
            raise AttributeError(
                "Final argument must be a dict of transaction parameters that "
                "includes a `from` field specifying the sender of the transaction"
            )

        return tx["from"].estimate_gas(amount=tx["value"], data=self.encode_input(*args))


class InterfaceContainer:
    """
    Container class that provides access to interfaces within a project.
    """

    def __init__(self, project: Any) -> None:
        self._project = project

        # automatically populate with interfaces in `data/interfaces`
        # overwritten if a project contains an interface with the same name
        for path in BROWNIE_FOLDER.glob("data/interfaces/*.json"):
            with path.open() as fp:
                abi = ujson_load(fp)
            self._add(path.stem, abi)

    def _add(self, name: ContractName, abi: list[ABIElement]) -> None:
        constructor = InterfaceConstructor(name, abi)
        setattr(self, name, constructor)


class InterfaceConstructor:
    """
    Constructor used to create Contract objects from a project interface.
    """

    def __init__(self, name: ContractName, abi: list[ABIElement]) -> None:
        self._name: Final = name
        self.abi: Final = abi
        self.selectors: Final[dict[Selector, FunctionName]] = {
            build_function_selector(i): FunctionName(build_function_signature(i)
           )
            for i in abi
           
            if i["type"] in ("function", "error", "event")
        }

    def __call__(self, address: str, owner: AccountsType | None = None) -> "Contract":
        return Contract.from_abi(self._name, address, self.abi, owner, persist=False)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} '{self._name}'>"

    def decode_input(self, calldata: str | bytes) -> tuple[str, Any]:
        """
        Decode input calldata for this contract.

        Arguments
        ---------
        calldata : str | bytes
            Calldata for a call to this contract

        Returns
        -------
        str
            Signature of the function that was called
        Any
            Decoded input arguments
        """
        if not isinstance(calldata, HexBytes):
            calldata = HexBytes(calldata)

        fn_selector = hexbytes_to_hexstring(calldata[:4])

        abi: ABIFunction | None = None
        for _abi in self.abi:
            if _abi["type"] in ("function", "error", "event") and build_function_selector(_abi) == fn_selector:
                abi = _abi
                break

        if abi is None:
            raise ValueError("Four byte selector does not match the ABI for this contract")

        function_sig = build_function_signature(abi)

        types_list = get_type_strings(abi["inputs"])
        result = decode_abi(types_list, calldata[4:])
        input_args = format_input(abi, result)

        return function_sig, input_args


class _DeployedContractBase(_ContractBase):
    """Methods for interacting with a deployed contract.

    Each public contract method is available as a ContractCall or ContractTx
    instance, created when this class is instantiated.

    Attributes:
        bytecode: Bytecode of the deployed contract, including constructor args.
        tx: TransactionReceipt of the of the tx that deployed the contract."""

    _reverted = False
    _initialized = False

    def __init__(
        self,
        address: HexAddress,
        owner: AccountsType | None = None,
        tx: TransactionReceiptType = None,
    ) -> None:
        address = _resolve_address(address)
        web3.isConnected()
        self.bytecode: Final[HexStr] = (  # type: ignore [assignment]
            # removeprefix is used for compatibility with both hexbytes<1 and >=1
            self._build.get("deployedBytecode", None) or web3.eth.get_code(address).hex().removeprefix("0x")
        )
        if not self.bytecode:
            raise ContractNotFound(f"No contract deployed at {address}")
        self._owner: Final = owner
        self.tx: Final = tx
        self.address: Final = address
        self.events = ContractEvents(self)
        _add_deployment_topics(address, self.abi)

        fn_abis = [abi for abi in self.abi if abi["type"] in ("function", "error", "event")]
        fn_names = [abi["name"] for abi in fn_abis]

        contract_name = self._name
        contract_natspec: dict = self._build.get("natspec") or {}
        methods_natspec: dict = contract_natspec.get("methods") or {}
        for abi, abi_name in zip(fn_abis, fn_names):
            name = f"{contract_name}.{abi_name}"
            sig = build_function_signature(abi)
            natspec = methods_natspec.get(sig, {})

            if fn_names.count(abi_name) == 1:
                fn = _get_method_object(address, abi, name, owner, natspec)
                self._check_and_set(abi_name, fn)
                continue

            # special logic to handle function overloading
            if not hasattr(self, abi_name):
                overloaded = OverloadedMethod(address, name, owner)
                self._check_and_set(abi_name, overloaded)
            getattr(self, abi_name)._add_fn(abi, natspec)

        self._initialized = True

    def _check_and_set(self, name: str, obj: Any) -> None:
        if name == "balance":
            warnings.warn(
                f"'{self._name}' defines a 'balance' function, "
                f"'{self._name}.balance' is available as {self._name}.wei_balance",
                BrownieEnvironmentWarning,
            )
            setattr(self, "wei_balance", self.balance)
        elif hasattr(self, name):
            warnings.warn(
                "Namespace collision between contract function and "
                f"brownie `Contract` class member: '{self._name}.{name}'\n"
                f"The {name} function will not be available when interacting with {self._name}",
                BrownieEnvironmentWarning,
            )
            return
        setattr(self, name, obj)

    def __hash__(self) -> int:
        return hash(f"{self._name}{self.address}{self._project}")

    def __str__(self) -> str:
        return self.address

    def __repr__(self) -> str:
        alias = self._build.get("alias")
        if alias:
            return f"<'{alias}' Contract '{self.address}'>"
        return f"<{self._name} Contract '{self.address}'>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _DeployedContractBase):
            return self.address == other.address and self.bytecode == other.bytecode
        if isinstance(other, str):
            try:
                address = _resolve_address(other)
                return address == self.address
            except ValueError:
                return False
        return super().__eq__(other)

    def __getattribute__(self, name: str) -> AnyContractMethod:
        if super().__getattribute__("_reverted"):
            raise ContractNotFound("This contract no longer exists.")
        try:
            return super().__getattribute__(name)
        except AttributeError:
            raise AttributeError(f"Contract '{self._name}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if self._initialized and isinstance(getattr(self, name, None), _ContractMethod):
            raise AttributeError(
                f"{self._name}.{name} is a contract function, it cannot be assigned to"
            )
        super().__setattr__(name, value)

    def get_method_object(self, calldata: str) -> Optional["_ContractMethod"]:
        """
        Given a calldata hex string, returns a `ContractMethod` object.
        """
        sig = calldata[:10].lower()
        if sig not in self.selectors:
            return None
        fn = getattr(self, self.selectors[sig], None)
        if isinstance(fn, OverloadedMethod):
            return next((v for v in fn.methods.values() if v.signature == sig), None)
        return fn

    def balance(self) -> Wei:
        """Returns the current ether balance of the contract, in wei."""
        web3.isConnected()
        balance = web3.eth.get_balance(self.address)
        return Wei(balance)

    def _deployment_path(self) -> Path | None:
        if not self._project._path or (
            CONFIG.network_type != "live" and not CONFIG.settings["dev_deployment_artifacts"]  # @UndefinedVariable
        ):
            return None

        chainid = CONFIG.active_network["chainid"] if CONFIG.network_type == "live" else "dev"  # @UndefinedVariable
        path = self._project._build_path.joinpath(f"deployments/{chainid}")
        path.mkdir(exist_ok=True)
        return path.joinpath(f"{self.address}.json")

    def _save_deployment(self) -> None:
        path = self._deployment_path()
        chainid = CONFIG.active_network["chainid"] if CONFIG.network_type == "live" else "dev"  # @UndefinedVariable
        deployment_build = self._build.copy()

        web3.isConnected()
        deployment_build["deployment"] = {
            "address": self.address,
            "chainid": chainid,
            "blockHeight": web3.eth.block_number,
        }
        if path:
            self._project._add_to_deployment_map(self)
            if not path.exists():
                with path.open("w") as fp:
                    ujson_dump(deployment_build, fp)

    def _delete_deployment(self) -> None:
        if path := self._deployment_path():
            self._project._remove_from_deployment_map(self)
            if path.exists():
                path.unlink()


class Contract(_DeployedContractBase):
    """
    Object to interact with a deployed contract outside of a project.
    """

    def __init__(
        self,
        address_or_alias: HexAddress | ContractName,
        *args: Any,
        owner: AccountsType | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Recreate a `Contract` object from the local database.

        The init method is used to access deployments that have already previously
        been stored locally. For new deployments use `from_abi` or `from_etherscan`.

        Arguments
        ---------
        address_or_alias : str
            Address or user-defined alias of the deployment.
        owner : Account, optional
            Contract owner. If set, transactions without a `from` field
            will be performed using this account.
        """
        address_or_alias = address_or_alias.strip()

        if args or kwargs:
            warnings.warn(
                "Initializing `Contract` in this manner is deprecated." " Use `from_abi` instead.",
                DeprecationWarning,
            )
            kwargs["owner"] = owner
            return self._deprecated_init(address_or_alias, *args, **kwargs)

        address = ""
        try:
            address = _resolve_address(address_or_alias)
            build, sources = _get_deployment(address)
        except Exception:
            build, sources = _get_deployment(alias=address_or_alias)
            if build is not None:
                address = build["address"]

        if build is None or sources is None:
            if (
                not address
                or not CONFIG.settings.get("autofetch_sources")  # @UndefinedVariable
                or not CONFIG.active_network.get("explorer")  # @UndefinedVariable
            ):
                if not address:
                    raise ValueError(f"Unknown alias: '{address_or_alias}'")
                else:
                    raise ValueError(f"Unknown contract address: '{address}'")
            contract = self.from_explorer(address, owner=owner, silent=True)
            build, sources = contract._build, contract._sources
            address = contract.address

        _ContractBase.__init__(self, None, build, sources)
        _DeployedContractBase.__init__(self, address, owner)

    def _deprecated_init(
        self,
        name: ContractName,
        address: HexAddress | None = None,
        abi: list[ABIElement] | None = None,
        manifest_uri: str | None = None,
        owner: AccountsType | None = None,
    ) -> None:
        if manifest_uri:
            raise ValueError("ethPM functionality removed")

        if not address:
            raise TypeError("Address cannot be None unless creating object from manifest")

        build = {"abi": abi, "contractName": name, "type": "contract"}
        _ContractBase.__init__(self, None, build, {})
        _DeployedContractBase.__init__(self, address, owner, None)

    @classmethod
    def from_abi(
        cls,
        name: ContractName,
        address: HexAddress,
        abi: list[ABIElement],
        owner: AccountsType | None = None,
        persist: bool = True,
    ) -> "Contract":
        """
        Create a new `Contract` object from an ABI.

        Arguments
        ---------
        name : str
            Name of the contract.
        address : str
            Address where the contract is deployed.
        abi : dict
            Contract ABI, given as a dictionary.
        owner : Account, optional
            Contract owner. If set, transactions without a `from` field
            will be performed using this account.
        """
        address = _resolve_address(address)
        try:
            # removeprefix is used for compatibility with both hexbytes<1 and >=1
            deployedBytecode = web3.eth.get_code(address).hex().removeprefix("0x")
        except Exception:
            # random junk that looks like bytecode
            deployedBytecode = (
                "6080"
                "ec29651ea57e9aa98bd340eba56e6b1fc767e9738a85fe35e62bad4993e36470"
                "e112d08934f17475f2fc5dfa78c8683663d623c1cca81c4426c55401ee3cb926"
                "f54d33f69d2f08e5ae55441c31256bc221eb4b9281537cf74c8ae5d3d4ae278e"
                "dd9f9b398ef414e5e3ec51883adbe3f48a006edcb8ec05db2a5dd84afe40816a"
                "1ccffe3910ca1c5d6371d0526e4ec6c65d58cd94c2458c33fe55fc4d4dcbf914"
                "3fc18a2704c01c6425d96fbada3a16c4151c2fb52ca6205ebae119a6bf4878d6"
                "54f7d0b19dbd90500d071af1a909a5835caaac19ea14b8e16d10a9912087b190"
                "fb56443789a17cb9569e80e345f20c1630ba179f2f48c0bfe5959953657f30ce"
                "b021ef313c177a1a32826720c1d20000f45e85f6db991266148c05a47e2640ff"
                "8aa04d6852af7eda7657d0c54449afd89f70df63b11adfc7bd81a1dca2daf0c5"
                "d53bb5c921f9c43bc20713dc0b2627640397124bdff4cf71e2a1e9f4f03d489f"
                "fd44cfb4fb6770336935d752d9d5b97514083b646ec945b067c70d19808af170"
                "66f9065cd7ebc5e120399d074a050e718d72da3752fc655b42ef3430f32e5ba8"
                "75df38d0b0dbe7ab4cd929f054777dc6cfe585d99156ae6f4a35ffc50d435d55"
                "df175523928f8e020377f8a8c5a321985f985985453b05ce69c8bc0117ca0fdb"
                "49fb92ddbb536079e4ca22547a1a15b193740f8e36be15c08fd8714a471f6327"
            )

        build = {
            "abi": abi,
            "address": address,
            "contractName": name,
            "type": "contract",
            "deployedBytecode": deployedBytecode,
        }

        self = cls.__new__(cls)
        _ContractBase.__init__(self, None, build, {})
        _DeployedContractBase.__init__(self, address, owner, None)
        if persist:
            _add_deployment(self)
        return self

    @classmethod
    def from_explorer(
        cls,
        address: HexAddress,
        as_proxy_for: str | None = None,
        owner: AccountsType | None = None,
        silent: bool = False,
        persist: bool = True,
    ) -> "Contract":
        """
        Create a new `Contract` object with source code queried from a block explorer.

        Arguments
        ---------
        address : str
            Address where the contract is deployed.
        as_proxy_for : str, optional
            Address of the implementation contract, if `address` is a proxy contract.
            The generated object will send transactions to `address`, but use the ABI
            and NatSpec of `as_proxy_for`. This field is only required when the
            block explorer API does not provide an implementation address.
        owner : Account, optional
            Contract owner. If set, transactions without a `from` field will be
            performed using this account.
        """
        address = _resolve_address(address)
        data = _fetch_from_explorer(address, "getsourcecode", silent)
        is_verified = bool(data["result"][0].get("SourceCode"))
        web3.isConnected()

        if is_verified:
            abi = ujson_loads(data["result"][0]["ABI"])
            name = data["result"][0]["ContractName"]
        else:
            # if the source is not available, try to fetch only the ABI
            try:
                data_abi = _fetch_from_explorer(address, "getabi", True)
            except ValueError as exc:
                _unverified_addresses.add(address)
                raise exc
            abi = ujson_loads(data_abi["result"].strip())
            name = "UnknownContractName"
            if not silent:
                warnings.warn(
                    f"{address}: Was able to fetch the ABI but not the source code. "
                    "Some functionality will not be available.",
                    BrownieCompilerWarning,
                )

        if as_proxy_for is None:
            # always check for an EIP1967 proxy - https://eips.ethereum.org/EIPS/eip-1967
            implementation_eip1967 = web3.eth.get_storage_at(
                address, int(web3.keccak(text="eip1967.proxy.implementation").hex(), 16) - 1
            )
            # always check for an EIP1822 proxy - https://eips.ethereum.org/EIPS/eip-1822
            implementation_eip1822 = web3.eth.get_storage_at(address, web3.keccak(text="PROXIABLE"))
            if len(implementation_eip1967) > 0 and int(implementation_eip1967.hex(), 16):
                as_proxy_for = _resolve_address(implementation_eip1967[-20:])
            elif len(implementation_eip1822) > 0 and int(implementation_eip1822.hex(), 16):
                as_proxy_for = _resolve_address(implementation_eip1822[-20:])
            elif data["result"][0].get("Implementation"):
                # for other proxy patterns, we only check if etherscan indicates
                # the contract is a proxy. otherwise we could have a false positive
                # if there is an `implementation` method on a regular contract.
                try:
                    # first try to call `implementation` per EIP897
                    # https://eips.ethereum.org/EIPS/eip-897
                    contract = cls.from_abi(name, address, abi)
                    as_proxy_for = contract.implementation.call()
                except Exception:
                    # if that fails, fall back to the address provided by etherscan
                    as_proxy_for = _resolve_address(data["result"][0]["Implementation"])

        if as_proxy_for == address:
            as_proxy_for = None

        # if this is a proxy, fetch information for the implementation contract
        if as_proxy_for is not None:
            implementation_contract = Contract.from_explorer(as_proxy_for)
            abi = implementation_contract._build["abi"]

        if not is_verified:
            return cls.from_abi(name, address, abi, owner)

        compiler_str = data["result"][0]["CompilerVersion"]
        if compiler_str.startswith("vyper:"):
            try:
                version = to_vyper_version(compiler_str[6:])
                is_compilable = version in get_installable_vyper_versions()
            except Exception:
                is_compilable = False
        else:
            try:
                version = cls.get_solc_version(compiler_str, address)

                is_compilable = (
                    version >= Version("0.4.22")
                    and version
                    in solcx.get_installable_solc_versions() + solcx.get_installed_solc_versions()
                )
            except Exception:
                is_compilable = False

        if not is_compilable:
            if not silent:
                warnings.warn(
                    f"{address}: target compiler '{compiler_str}' cannot be installed or is not "
                    "supported by Brownie. Some debugging functionality will not be available.",
                    BrownieCompilerWarning,
                )
            return cls.from_abi(name, address, abi, owner)
        elif data["result"][0]["OptimizationUsed"] in ("true", "false"):
            if not silent:
                warnings.warn(
                    "Blockscout explorer API has limited support by Brownie. "  # noqa
                    "Some debugging functionality will not be available.",
                    BrownieCompilerWarning,
                )
            return cls.from_abi(name, address, abi, owner)

        optimizer = {
            "enabled": bool(int(data["result"][0]["OptimizationUsed"])),
            "runs": int(data["result"][0]["Runs"]),
        }
        evm_version = data["result"][0].get("EVMVersion", "Default")
        if evm_version == "Default":
            evm_version = None

        source_str = "\n".join(data["result"][0]["SourceCode"].splitlines())
        try:
            if source_str.startswith("{{"):
                # source was verified using compiler standard JSON
                input_json = ujson_loads(source_str[1:-1])
                sources = {k: v["content"] for k, v in input_json["sources"].items()}
                evm_version = input_json["settings"].get("evmVersion", evm_version)
                remappings = input_json["settings"].get("remappings", [])

                compiler.set_solc_version(str(version))
                input_json.update(
                    compiler.generate_input_json(
                        sources, optimizer=optimizer, evm_version=evm_version, remappings=remappings
                    )
                )
                output_json = compiler.compile_from_input_json(input_json)
                build_json = compiler.generate_build_json(input_json, output_json)
            else:
                if source_str.startswith("{"):
                    # source was submitted as multiple files
                    sources = {k: v["content"] for k, v in ujson_loads(source_str).items()}
                else:
                    # source was submitted as a single file
                    if compiler_str.startswith("vyper"):
                        path_str = f"{name}.vy"
                    else:
                        path_str = f"{name}-flattened.sol"
                    sources = {path_str: source_str}

                build_json = compiler.compile_and_format(
                    sources,
                    solc_version=str(version),
                    vyper_version=str(version),
                    optimizer=optimizer,
                    evm_version=evm_version,
                )
        except Exception as e:
            if not silent:
                warnings.warn(
                    f"{address}: Compilation failed due to {type(e).__name__}. Falling back to ABI,"
                    " some functionality will not be available.",
                    BrownieCompilerWarning,
                )
            return cls.from_abi(name, address, abi, owner)

        build_json = build_json[name]
        if as_proxy_for is not None:
            build_json.update(abi=abi, natspec=implementation_contract._build.get("natspec"))

        if not _verify_deployed_code(
            address, build_json["deployedBytecode"], build_json["language"]
        ):
            if not silent:
                warnings.warn(
                    f"{address}: Locally compiled and on-chain bytecode do not match!",
                    BrownieCompilerWarning,
                )
            del build_json["pcMap"]

        self = cls.__new__(cls)
        _ContractBase.__init__(self, None, build_json, sources)
        _DeployedContractBase.__init__(self, address, owner)
        if persist:
            _add_deployment(self)
        return self

    @classmethod
    def get_solc_version(cls, compiler_str: str, address: str) -> Version: # type: ignore
        """
        Return the solc compiler version either from the passed compiler string
        or try to find the latest available patch semver compiler version.

        Arguments
        ---------
        compiler_str: str
            The compiler string passed from the contract metadata.
        address: str
            The contract address to check for.
        """
        version = Version(compiler_str.lstrip("v")).truncate()

        compiler_config = _load_project_compiler_config(Path(os.getcwd()))
        solc_config = compiler_config["solc"]
        if "use_latest_patch" in solc_config:
            use_latest_patch = solc_config["use_latest_patch"]
            needs_patch_version = False
            if isinstance(use_latest_patch, bool):
                needs_patch_version = use_latest_patch
            elif isinstance(use_latest_patch, list):
                needs_patch_version = address in use_latest_patch

            if needs_patch_version:
                versions = [Version(str(i)) for i in solcx.get_installable_solc_versions()]
                for v in filter(lambda x: x < version.next_minor(), versions):
                    if v > version:
                        version = v

        return version

    @classmethod
    def remove_deployment(
        cls,
        address: ChecksumAddress | None = None,
        alias: ContractName | None = None,
    ) -> tuple[dict | None, dict | None]:
        """
        Removes this contract from the internal deployments db
        with the passed address or alias.

        Arguments
        ---------
        address: str | None
            An address to apply
        alias: str | None
            An alias to apply
        """
        return _remove_deployment(address, alias)

    def set_alias(self, alias: str | None, persist: bool = True) -> None:
        """
        Apply a unique alias this object. The alias can be used to restore the
        object in future sessions.

        Arguments
        ---------
        alias: str | None
            An alias to apply. If `None`, any existing alias is removed.
        """
        if "chainid" not in CONFIG.active_network:  # @UndefinedVariable
            raise ValueError("Cannot set aliases in a development environment")

        if alias is not None:
            if "." in alias or alias.lower().startswith("0x"):
                raise ValueError("Invalid alias")
            build, _ = _get_deployment(alias=alias)
            if build is not None:
                if build["address"] != self.address:
                    raise ValueError("Alias is already in use on another contract")
                return

        if persist:
            _add_deployment(self, alias)
        self._build["alias"] = alias

    @property
    def alias(self) -> str | None:
        return self._build.get("alias")


class ProjectContract(_DeployedContractBase):
    """Methods for interacting with a deployed contract as part of a Brownie project."""

    def __init__(
        self,
        project: Any,
        build: ContractBuildJson,
        address: ChecksumAddress,
        owner: AccountsType | None = None,
        tx: TransactionReceiptType = None,
    ) -> None:
        _ContractBase.__init__(self, project, build, project._sources)
        _DeployedContractBase.__init__(self, address, owner, tx)


class ContractEvents(_ContractEvents):
    def __init__(self, contract: _DeployedContractBase):
        self.linked_contract = contract

        # Ignoring type since ChecksumAddress type is an alias for string
        _ContractEvents.__init__(self, contract.abi, web3, contract.address)

    def subscribe(
        self, event_name: str, callback: Callable[[AttributeDict], None], delay: float = 2.0
    ) -> None:
        """
        Subscribe to event with a name matching 'event_name', calling the 'callback'
        function on new occurrence giving as parameter the event log receipt.

        Args:
            event_name (str): Name of the event to subscribe to.
            callback (Callable[[AttributeDict], None]): Function called whenever an event occurs.
            delay (float, optional): Delay between each check for new events. Defaults to 2.0.
        """
        target_event: ContractEvent = self.__getitem__(event_name)
        event_watcher.add_event_callback(event=target_event, callback=callback, delay=delay)

    def get_sequence(
        self, from_block: int, to_block: int = None, event_type: ContractEvent | str = None
    ) -> list[AttributeDict] | AttributeDict:
        """Returns the logs of events of type 'event_type' that occurred between the
        blocks 'from_block' and 'to_block'. If 'event_type' is not specified,
        it retrieves the occurrences of all events in the contract.

        Args:
            from_block (int): The block from which to search for events that have occurred.
            to_block (int, optional): The block on which to stop searching for events.
            if not specified, it is set to the most recently mined block (web3.eth.block_number).
            Defaults to None.
            event_type (ContractEvent, str, optional): Type or name of the event to be searched
            between the specified blocks. Defaults to None.

        Returns:
            if 'event_type' is specified:
                [list]: List of events of type 'event_type' that occurred between
                'from_block' and 'to_block'.
            else:
                event_logbook [dict]: Dictionary of events of the contract that occurred
                between 'from_block' and 'to_block'.
        """
        web3.isConnected()
        if to_block is None or to_block > web3.eth.block_number:
            to_block = web3.eth.block_number

        # Returns event sequence for the specified event
        if event_type is not None:
            if isinstance(event_type, str):
                # If 'event_type' is a string, search for an event with a name matching it.
                event_type: ContractEvent = self.__getitem__(event_type)
            return self._retrieve_contract_events(event_type, from_block, to_block)

        return AttributeDict(
            (event.event_name, self._retrieve_contract_events(event, from_block, to_block))
            for event in ContractEvents.__iter__(self)
        )

    def listen(self, event_name: str, timeout: float = 0) -> Coroutine:
        """
        Creates a listening Coroutine object ending whenever an event matching
        'event_name' occurs. If timeout is superior to zero and no event matching
        'event_name' has occurred, the Coroutine ends when the timeout is reached.

        The Coroutine return value is an AttributeDict filled with the following fields :
            - 'event_data' (AttributeDict): The event log receipt that was caught.
            - 'timed_out' (bool): False if the event did not timeout, else True

        If the 'timeout' parameter is not passed or is inferior or equal to 0,
        the Coroutine listens indefinitely.

        Args:
            event_name (str): Name of the event to be listened to.
            timeout (float, optional): Timeout value in seconds. Defaults to 0.

        Returns:
            Coroutine: Awaitable object listening for the event matching 'event_name'.
        """
        _triggered: bool = False
        _received_data: AttributeDict | None = None

        def _event_callback(event_data: AttributeDict) -> None:
            """
            Fills the nonlocal variable '_received_data' with the received
            argument 'event_data' and sets the nonlocal '_triggered' variable to True
            """
            nonlocal _triggered, _received_data
            _received_data = event_data
            _triggered = True

        _listener_end_time = time.time() + timeout

        async def _listening_task(is_timeout: bool, end_time: float) -> AttributeDict:
            """Generates and returns a coroutine listening for an event"""
            nonlocal _triggered, _received_data
            timed_out: bool = False

            while not _triggered:
                if is_timeout and end_time <= time.time():
                    timed_out = True
                    break
                await asyncio.sleep(0.05)
            return AttributeDict({"event_data": _received_data, "timed_out": timed_out})

        target_event: ContractEvent = self.__getitem__(event_name)
        event_watcher.add_event_callback(
            event=target_event, callback=_event_callback, delay=0.2, repeat=False
        )
        return _listening_task(timeout > 0, _listener_end_time)

    @combomethod
    def _retrieve_contract_events(
        self, event_type: ContractEvent, from_block: int = None, to_block: int = None
    ) -> list[LogReceipt]:
        """
        Retrieves all log receipts from 'event_type' between 'from_block' and 'to_block' blocks
        """
        if to_block is None:
            web3.isConnected()
            to_block = web3.eth.block_number
        if from_block is None and isinstance(to_block, int):
            from_block = to_block - 10

        event_filter: filters.LogFilter = event_type.create_filter(
            fromBlock=from_block, toBlock=to_block
        )
        return event_filter.get_all_entries()


class OverloadedMethod:
    def __init__(self, address: ChecksumAddress, name: str, owner: AccountsType | None):
        self._address: Final = address
        self._name: Final = name
        self._owner: Final = owner
        self.methods: Final[dict[Any, ContractCall | ContractTx]] = {}
        self.natspec: Final[dict[str, Any]] = {}

    def _add_fn(self, abi: ABIFunction, natspec: dict[str, Any]) -> None:
        fn = _get_method_object(self._address, abi, self._name, self._owner, natspec)
        key = tuple(i["type"].replace("256", "") for i in abi["inputs"])
        self.methods[key] = fn
        self.natspec.update(natspec)

    def _get_fn_from_args(self, args: tuple) -> "_ContractMethod":
        input_length = len(args)
        if args and isinstance(args[-1], dict):
            input_length -= 1
        keys = [i for i in self.methods if len(i) == input_length]
        if not keys:
            raise ValueError("No function matching the given number of arguments")
        if len(keys) > 1:
            raise ValueError(
                f"Contract has more than one function '{self._name}' requiring "
                f"{input_length} arguments. You must explicitly declare which function "
                f"you are calling, e.g. {self._name}['{','.join(keys[0])}'](*args)"
            )
        return self.methods[keys[0]]

    def __getitem__(self, key: tuple[str, ...] | str) -> Union["ContractCall", "ContractTx"]:
        if isinstance(key, str):
            key = (i.strip() for i in key.split(","))

        key = tuple(i.replace("256", "") for i in key)
        return self.methods[key]

    def __repr__(self) -> str:
        return f"<OverloadedMethod '{self._name}'>"

    def __len__(self) -> int:
        return len(self.methods)

    def __call__(
        self, *args: Any, block_identifier: int | str | bytes = None, override: dict = None
    ) -> Any:
        fn = self._get_fn_from_args(args)
        kwargs = {"block_identifier": block_identifier, "override": override}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return fn(*args, **kwargs)

    def call(
        self, *args: Any, block_identifier: int | str | bytes = None, override: dict = None
    ) -> Any:
        """
        Call the contract method without broadcasting a transaction.

        The specific function called is chosen based on the number of
        arguments given. If more than one function exists with this number
        of arguments, a `ValueError` is raised.

        Arguments
        ---------
        *args
            Contract method inputs. You can optionally provide a
            dictionary of transaction properties as the last arg.
        block_identifier : int | str | bytes, optional
            A block number or hash that the call is executed at. If not given, the
            latest block used. Raises `ValueError` if this value is too far in the
            past and you are not using an archival node.
        override : dict, optional
            A mapping from addresses to balance, nonce, code, state, stateDiff
            overrides for the context of the call.

        Returns
        -------
            Contract method return value(s).
        """
        fn = self._get_fn_from_args(args)
        return fn.call(*args, block_identifier=block_identifier, override=override)

    def transact(self, *args: Any) -> TransactionReceiptType:
        """
        Broadcast a transaction that calls this contract method.

        The specific function called is chosen based on the number of
        arguments given. If more than one function exists with this number
        of arguments, a `ValueError` is raised.

        Arguments
        ---------
        *args
            Contract method inputs. You can optionally provide a
            dictionary of transaction properties as the last arg.

        Returns
        -------
        TransactionReceipt
            Object representing the broadcasted transaction.
        """
        fn = self._get_fn_from_args(args)
        return fn.transact(*args)

    def encode_input(self, *args: Any) -> Any:
        """
        Generate encoded ABI data to call the method with the given arguments.

        Arguments
        ---------
        *args
            Contract method inputs

        Returns
        -------
        str
            Hexstring of encoded ABI data
        """
        fn = self._get_fn_from_args(args)
        return fn.encode_input(*args)

    def decode_input(self, hexstr: str) -> list:
        """
        Decode input call data for this method.

        Arguments
        ---------
        hexstr : str
            Hexstring of input call data

        Returns
        -------
        Decoded values
        """
        selector = hexbytes_to_hexstring(HexBytes(hexstr)[:4])
        for fn in self.methods.values():
            if fn == selector:
                return fn.decode_input(hexstr)
        raise ValueError(
            "Data cannot be decoded using any input signatures of functions of this name"
        )

    def decode_output(self, hexstr: str) -> tuple:
        """
        Decode hexstring data returned by this method.

        Arguments
        ---------
        hexstr : str
            Hexstring of returned call data

        Returns
        -------
        Decoded values
        """
        for fn in self.methods.values():
            try:
                return fn.decode_output(hexstr)
            except Exception:
                pass
        raise ValueError(
            "Data cannot be decoded using any output signatures of functions of this name"
        )

    def info(self) -> None:
        """
        Display NatSpec documentation for this method.
        """
        fn_sigs = (f"{fn.abi['name']}({_inputs(fn.abi)})" for fn in self.methods.values())
        for sig in sorted(fn_sigs, key=lambda k: len(k)):
            print(sig)
        _print_natspec(self.natspec)

class _ContractFragment:
    _dir_color: Final = "bright magenta"

    def __init__(
        self,
        address: ChecksumAddress,
        abi: ABIFunction,
        name: str,
        owner: AccountsType | None,
        natspec: dict[str, Any] | None = None,
    ) -> None:
        self._address: Final = address
        self._name: Final = name
        self.abi: Final = abi
        self._owner: Final = owner
        self.signature: Final = build_function_selector(abi)
        self._input_sig: Final = build_function_signature(abi)
        self.natspec: Final[dict[str, Any]] = natspec or {}

    def info(self) -> None:
        """
        Display NatSpec documentation for this method.
        """
        print(f"{self.abi['name']}({_inputs(self.abi)})")
        _print_natspec(self.natspec)

    def decode_input(self, hexstr: str) -> list:
        """
        Decode input call data for this method.

        Arguments
        ---------
        hexstr : str
            Hexstring of input call data

        Returns
        -------
        Decoded values
        """
        abi = self.abi
        types_list = get_type_strings(abi["inputs"])
        result = decode_abi(types_list, HexBytes(hexstr)[4:])
        return format_input(abi, result)

    def encode_input(self, *args: Any) -> str:
        """
        Generate encoded ABI data to call the method with the given arguments.

        Arguments
        ---------
        *args
            Contract method inputs

        Returns
        -------
        str
            Hexstring of encoded ABI data
        """
        abi = self.abi
        data = format_input(abi, args)
        types_list = get_type_strings(abi["inputs"])
        return self.signature + encode_abi(types_list, data).hex()

    def decode_output(self, hexstr: str) -> tuple:
        """
        Decode hexstring data returned by this method.

        Arguments
        ---------
        hexstr : str
            Hexstring of returned call data

        Returns
        -------
        Decoded values
        """
        abi = self.abi
        types_list = get_type_strings(abi["outputs"])
        result = decode_abi(types_list, HexBytes(hexstr))
        result = format_output(abi, result)
        if len(result) == 1:
            result = result[0]
        return result
    

class ContractEventError(_ContractFragment):
    def __repr__(self) -> str:
        return f"<{self.abi['type']} '{self.abi['name']}({_inputs(self.abi)})'>"


class _ContractMethod(_ContractFragment):
    def __repr__(self) -> str:
        pay = "payable " if self.payable else ""
        return f"<{type(self).__name__} {pay}'{self.abi['name']}({_inputs(self.abi)})'>"

    @property
    def payable(self) -> bool:
        abi = self.abi
        if "payable" in abi:
            return abi["payable"]
        else:
            return abi["stateMutability"] == "payable"

    @staticmethod
    def _autosuggest(obj: "_ContractMethod") -> list[str]:
        # this is a staticmethod to be compatible with `_call_suggest` and `_transact_suggest`
        return _contract_method_autosuggest(
            obj.abi["inputs"], isinstance(obj, ContractTx), obj.payable
        )

    def info(self) -> None:
        """
        Display NatSpec documentation for this method.
        """
        abi = self.abi
        print(f"{abi['name']}({_inputs(abi)})")
        _print_natspec(self.natspec)

    def call(
        self, *args: Any, block_identifier: Optional[int | str | bytes] = None, override: Optional[dict] = None, max_retries=5
    ) -> Any:
        """
        Call the contract method without broadcasting a transaction.

        Arguments
        ---------
        *args
            Contract method inputs. You can optionally provide a
            dictionary of transaction properties as the last arg.
        block_identifier : int | str | bytes, optional
            A block number or hash that the call is executed at. If not given, the
            latest block used. Raises `ValueError` if this value is too far in the
            past and you are not using an archival node.
        override : dict, optional
            A mapping from addresses to balance, nonce, code, state, stateDiff
            overrides for the context of the call.

        Returns
        -------
            Contract method return value(s).
        """

        try:
            args, tx = _get_tx(self._owner, args)
            if tx["from"]:
                tx["from"] = str(tx["from"])
            del tx["required_confs"]
            tx.update({"to": self._address, "data": self.encode_input(*args)})

            try:
                web3.isConnected()
                data = web3.eth.call({k: v for k, v in tx.items() if v}, block_identifier, override)
            except ValueError as e:
                raise VirtualMachineError(e) from None

            if self.abi["outputs"] and not data:
                raise ValueError("No data was returned - the call likely reverted")
            try:
                return self.decode_output(data)
            except Exception:
                raise ValueError(f"Call reverted: {decode_typed_error(data)}") from None
        except Exception:
            if max_retries <= 0:
                raise

            time.sleep(_rng.random() * 0.4 + 0.1)
            return self.call(*args, block_identifier=block_identifier, override=override, max_retries=max_retries - 1)

    def transact(self, *args: Any, silent: bool = False) -> TransactionReceiptType:
        """
        Broadcast a transaction that calls this contract method.

        Arguments
        ---------
        *args
            Contract method inputs. You can optionally provide a
            dictionary of transaction properties as the last arg.

        Returns
        -------
        TransactionReceipt
            Object representing the broadcasted transaction.
        """

        args, tx = _get_tx(self._owner, args)
        if not tx["from"]:
            raise AttributeError(
                "Final argument must be a dict of transaction parameters that "
                "includes a `from` field specifying the sender of the transaction"
            )
        
        print(f"{tx['from'].address}: calling {self._name}{args}")

        return tx["from"].transfer(
            self._address,
            tx["value"],
            gas_limit=tx["gas"],
            gas_buffer=tx.get("gas_buffer"),
            gas_price=tx.get("gas_price"),
            max_fee=tx.get("max_fee"),
            priority_fee=tx.get("priority_fee"),
            nonce=tx["nonce"],
            required_confs=tx["required_confs"],
            data=self.encode_input(*args),
            allow_revert=tx["allow_revert"],
            silent=silent,
            test_function=tx.get("test_function"),
            max_retries=tx.get("max_retries", 5),
        )

    def decode_input(self, hexstr: str) -> list:
        """
        Decode input call data for this method.

        Arguments
        ---------
        hexstr : str
            Hexstring of input call data

        Returns
        -------
        Decoded values
        """
        abi = self.abi
        types_list = get_type_strings(abi["inputs"])
        result = decode_abi(types_list, HexBytes(hexstr)[4:])
        return format_input(abi, result)

    def encode_input(self, *args: Any) -> str:
        """
        Generate encoded ABI data to call the method with the given arguments.

        Arguments
        ---------
        *args
            Contract method inputs

        Returns
        -------
        str
            Hexstring of encoded ABI data
        """
        abi = self.abi
        data = format_input(abi, args)
        types_list = get_type_strings(abi["inputs"])
        return self.signature + encode_abi(types_list, data).hex()

    def decode_output(self, hexstr: str) -> tuple:
        """
        Decode hexstring data returned by this method.

        Arguments
        ---------
        hexstr : str
            Hexstring of returned call data

        Returns
        -------
        Decoded values
        """
        abi = self.abi
        types_list = get_type_strings(abi["outputs"])
        result = decode_abi(types_list, HexBytes(hexstr))
        result = format_output(abi, result)
        if len(result) == 1:
            result = result[0]
        return result

    def estimate_gas(self, *args: Any) -> int:
        """
        Estimate the gas cost for a transaction.

        Raises VirtualMachineError if the transaction would revert.

        Arguments
        ---------
        *args
            Contract method inputs

        Returns
        -------
        int
            Estimated gas value in wei.
        """
        args, tx = _get_tx(self._owner, args)
        if not tx["from"]:
            raise AttributeError(
                "Final argument must be a dict of transaction parameters that "
                "includes a `from` field specifying the sender of the transaction"
            )

        return tx["from"].estimate_gas(
            to=self._address,
            amount=tx["value"],
            data=self.encode_input(*args),
        )


class ContractTx(_ContractMethod):
    """
    A public payable or non-payable contract method.

    Attributes
    ----------
    abi : dict
        Contract ABI specific to this method.
    signature : str
        Bytes4 method signature.
    """

    def __call__(self, *args: Any, silent: bool = False) -> TransactionReceiptType:
        """
        Broadcast a transaction that calls this contract method.

        Arguments
        ---------
        *args
            Contract method inputs. You can optionally provide a
            dictionary of transaction properties as the last arg.

        Returns
        -------
        TransactionReceipt
            Object representing the broadcasted transaction.
        """

        return self.transact(*args, silent=silent)


class ContractCall(_ContractMethod):
    """
    A public view or pure contract method.

    Attributes
    ----------
    abi : dict
        Contract ABI specific to this method.
    signature : str
        Bytes4 method signature.
    """

    def __call__(
        self, *args: Any, block_identifier: int | str | bytes = None, override: dict = None
    ) -> Any:
        """
        Call the contract method without broadcasting a transaction.

        Arguments
        ---------
        args
            Contract method inputs. You can optionally provide a
            dictionary of transaction properties as the last arg.
        block_identifier : int | str | bytes, optional
            A block number or hash that the call is executed at. If not given, the
            latest block used. Raises `ValueError` if this value is too far in the
            past and you are not using an archival node.
        override : dict, optional
            A mapping from addresses to balance, nonce, code, state, stateDiff
            overrides for the context of the call.

        Returns
        -------
            Contract method return value(s).
        """
        try:
            if not CONFIG.argv["always_transact"] or block_identifier is not None:
                return self.call(*args, block_identifier=block_identifier, override=override)

            args, tx = _get_tx(self._owner, args)
            tx.update({"gas_price": 0, "from": self._owner or accounts[0]})
            pc, revert_msg = None, None

            try:
                self.transact(*args, tx)
                chain.undo()
            except VirtualMachineError as exc:
                pc, revert_msg = exc.pc, exc.revert_msg
                chain.undo()
            except Exception:
                pass

            try:
                return self.call(*args)
            except VirtualMachineError as exc:
                if pc == exc.pc and revert_msg and exc.revert_msg is None:
                    # in case we miss a dev revert string
                    exc.revert_msg = revert_msg
                raise exc
        except Exception as ex:
            print(f"Caught {ex} calling {self.abi['name']}({args}) on {self._address}")
            raise ex


def _get_tx(owner: AccountsType | None, args: tuple) -> tuple:
    # set / remove default sender
    if owner is None:
        owner = accounts.default
    default_owner = CONFIG.active_network["settings"]["default_contract_owner"]  # @UndefinedVariable
    if CONFIG.mode == "test" and default_owner is False:  # @UndefinedVariable
        owner = None

    # separate contract inputs from tx dict and set default tx values
    tx = {
        "from": owner,
        "value": 0,
        "gas": None,
        "gas_buffer": None,
        "nonce": None,
        "required_confs": 1,
        "allow_revert": None,
    }
    if args and isinstance(args[-1], dict):
        tx.update(args[-1])
        args = args[:-1]
        # key substitution to provide compatibility with web3.py
        for key, target in [("amount", "value"), ("gas_limit", "gas"), ("gas_price", "gasPrice")]:
            if key in tx:
                tx[target] = tx[key]

    # enable the magic of ganache's `evm_unlockUnknownAccount`
    if isinstance(tx["from"], str):
        tx["from"] = accounts.at(tx["from"], force=True)
    elif isinstance(tx["from"], _DeployedContractBase):
        tx["from"] = accounts.at(tx["from"].address, force=True)

    return args, tx


def _get_method_object(
    address: ChecksumAddress,
    abi: ABIFunction,
    name: str,
    owner: AccountsType | None,
    natspec: dict[str, Any],
) -> ContractCall | ContractTx:
    if abi["type"] in ("error", "event"):
        return ContractEventError(address, abi, name, owner, natspec)
    
    if "constant" in abi:
        constant = abi["constant"]
    else:
        constant = abi["stateMutability"] in ("view", "pure")

    if constant:
        return ContractCall(address, abi, name, owner, natspec)
    return ContractTx(address, abi, name, owner, natspec)


_fixed168x10: Final = {"fixed168x10": "decimal"}


def _inputs(abi: ABIFunction | ABIConstructor) -> str:
    abi_inputs = abi["inputs"]
    types_list = get_type_strings(abi_inputs, _fixed168x10)
    return ", ".join(
        f"{types}{bright_blue}{f' {name}' if name else ''}{color}"
        for name, types in zip((i["name"] for i in abi_inputs), types_list)
    )


def _verify_deployed_code(
    address: ChecksumAddress, expected_bytecode: HexStr, language: Language
) -> bool:
    web3.isConnected()
    # removeprefix is used for compatibility with both hexbytes<1 and >=1
    actual_bytecode = web3.eth.get_code(address).hex().removeprefix("0x")
    expected_bytecode = expected_bytecode.removeprefix("0x")

    if expected_bytecode.startswith("730000000000000000000000000000000000000000"):
        # special case for Solidity libraries
        return (
            actual_bytecode.startswith(f"73{address[2:].lower()}")
            and actual_bytecode[42:] == expected_bytecode[42:]
        )

    if "_" in expected_bytecode:
        for marker in regex_findall("_{1,}[^_]*_{1,}", expected_bytecode):
            idx = expected_bytecode.index(marker)
            actual_bytecode = actual_bytecode[:idx] + actual_bytecode[idx + 40 :]
            expected_bytecode = expected_bytecode[:idx] + expected_bytecode[idx + 40 :]

    if language == "Solidity":
        # do not include metadata in comparison
        idx = -(int(actual_bytecode[-4:], 16) + 2) * 2
        actual_bytecode = actual_bytecode[:idx]
        idx = -(int(expected_bytecode[-4:], 16) + 2) * 2
        expected_bytecode = expected_bytecode[:idx]

    if language == "Vyper":
        # don't check immutables section
        # TODO actually grab data section length from layout.
        return actual_bytecode.startswith(expected_bytecode)

    return actual_bytecode == expected_bytecode


def _print_natspec(natspec: dict[str, Any]) -> None:
    wrapper = TextWrapper(initial_indent=f"  {bright_magenta}")
    for key in ("title", "notice", "author", "details"):
        if key in natspec:
            wrapper.subsequent_indent = " " * (len(key) + 4)
            print(wrapper.fill(f"@{key} {color}{natspec[key]}"))

    for key, value in natspec.get("params", {}).items():
        wrapper.subsequent_indent = " " * 9
        print(wrapper.fill(f"@param {bright_blue}{key}{color} {value}"))

    if "return" in natspec:
        wrapper.subsequent_indent = " " * 10
        print(wrapper.fill(f"@return {color}{natspec['return']}"))

    for key in sorted(natspec.get("returns", [])):
        wrapper.subsequent_indent = " " * 10
        print(wrapper.fill(f"@return {color}{natspec['returns'][key]}"))

    print()


def _fetch_from_explorer(address: ChecksumAddress, action: str, silent: bool) -> dict[str, Any]:
    if address in _unverified_addresses:
        raise ValueError(f"Source for {address} has not been verified")

    web3.isConnected()
    # removeprefix is used for compatibility with both hexbytes<1 and >=1
    code = web3.eth.get_code(address).hex().removeprefix("0x")
    # EIP-1167: Minimal Proxy Contract
    if code[:20] == "363d3d373d3d3d363d73" and code[60:] == "5af43d82803e903d91602b57fd5bf3":
        address = _resolve_address(code[20:60])
    # Vyper <0.2.9 `create_forwarder_to`
    elif (
        code[:30] == "366000600037611000600036600073"
        and code[70:] == "5af4602c57600080fd5b6110006000f3"
    ):
        address = _resolve_address(code[30:70])
    # 0xSplits Clones
    elif (
        code[:120]
        == "36603057343d52307f830d2d700a97af574b186c80d40429385d24241565b08a7c559ba283a964d9b160203da23d3df35b3d3d3d3d363d3d37363d73"  # noqa e501
        and code[160:] == "5af43d3d93803e605b57fd5bf3"
    ):
        address = _resolve_address(code[120:160])

    params: dict[str, Any] = {
        "module": "contract",
        "action": action,
        "address": address,
        "chainid": web3.chain_id,
    }
    env_key = os.getenv("ETHERSCAN_TOKEN")
    if env_key is not None:
        params["apiKey"] = env_key
    elif not silent:
        warnings.warn(
            "No ETHERSCAN_API token set. You may experience issues with rate limiting. "
            "Visit https://etherscan.io/register to obtain a token, and then store it "
            "as the environment variable $ETHERSCAN_TOKEN",
            BrownieEnvironmentWarning,
        )
    if not silent:
        print(f"Fetching source of {bright_blue}{address}{color} from Etherscan...")

    response = requests.get(
        "https://api.etherscan.io/v2/api", params=params, headers=REQUEST_HEADERS
    )
    if response.status_code != 200:
        raise ConnectionError(
            f"Status {response.status_code} when querying Etherscan: {response.text}"
        )
    data = response.json()
    if int(data["status"]) != 1:
        raise ValueError(f"Failed to retrieve data from API: {data}")

    return data


# console auto-completion logic


def _call_autosuggest(method: ContractCall | ContractTx) -> list[str]:
    # since methods are not unique for each object, we use `__reduce__`
    # to locate the specific object so we can access the correct ABI
    method = method.__reduce__()[1][0]
    return _contract_method_autosuggest(method.abi["inputs"], False, False)


def _transact_autosuggest(method: ContractCall | ContractTx) -> list[str]:
    method = method.__reduce__()[1][0]
    return _contract_method_autosuggest(method.abi["inputs"], True, method.payable)


# assign the autosuggest functionality to various methods
ContractConstructor.encode_input.__dict__["_autosuggest"] = _call_autosuggest
_ContractMethod.call.__dict__["_autosuggest"] = _call_autosuggest
_ContractMethod.encode_input.__dict__["_autosuggest"] = _call_autosuggest

ContractConstructor.estimate_gas.__dict__["_autosuggest"] = _transact_autosuggest
_ContractMethod.estimate_gas.__dict__["_autosuggest"] = _transact_autosuggest
_ContractMethod.transact.__dict__["_autosuggest"] = _transact_autosuggest


def _contract_method_autosuggest(
    args: list[dict[str, Any]], is_transaction: bool, is_payable: bool
) -> list[str]:
    types_list = get_type_strings(args, _fixed168x10)
    names = (i["name"] for i in args)
    suggestions = [f" {typ}{f' {name}' if name else ''}" for name, typ in zip(names, types_list)]
    if is_transaction:
        if is_payable:
            suggestions.append(" {'from': Account", " 'value': Wei}")
        else:
            suggestions.append(" {'from': Account}")
    return suggestions


def _comment_slicer(match: Match) -> str:
    start, mid, end = match.group(1, 2, 3)
    if mid is None:
        # single line comment
        return ""
    elif start is not None or end is not None:
        # multi line comment at start or end of a line
        return ""
    elif "\n" in mid:
        # multi line comment with line break
        return "\n"
    else:
        # multi line comment without line break
        return " "
