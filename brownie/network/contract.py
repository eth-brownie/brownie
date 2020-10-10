#!/usr/bin/python3

import json
import os
import re
import warnings
from pathlib import Path
from textwrap import TextWrapper
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

import eth_abi
import requests
import solcx
from eth_utils import remove_0x_prefix
from hexbytes import HexBytes
from semantic_version import Version
from vvm import get_installable_vyper_versions
from vvm.utils.convert import to_vyper_version

from brownie._config import BROWNIE_FOLDER, CONFIG, REQUEST_HEADERS
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
)
from brownie.project import compiler, ethpm
from brownie.typing import AccountsType, TransactionReceiptType
from brownie.utils import color

from . import accounts, chain
from .event import _add_deployment_topics, _get_topics
from .state import (
    _add_contract,
    _add_deployment,
    _find_contract,
    _get_deployment,
    _remove_contract,
    _revert_register,
)
from .web3 import _resolve_address, web3

_unverified_addresses: Set = set()


class _ContractBase:

    _dir_color = "bright magenta"

    def __init__(self, project: Any, build: Dict, sources: Dict) -> None:
        self._project = project
        self._build = build.copy()
        self._sources = sources
        self.topics = _get_topics(self.abi)
        self.selectors = {
            build_function_selector(i): i["name"] for i in self.abi if i["type"] == "function"
        }
        # this isn't fully accurate because of overloaded methods - will be removed in `v2.0.0`
        self.signatures = {
            i["name"]: build_function_selector(i) for i in self.abi if i["type"] == "function"
        }

    @property
    def abi(self) -> List:
        return self._build["abi"]

    @property
    def _name(self) -> str:
        return self._build["contractName"]

    def info(self) -> None:
        """
        Display NatSpec documentation for this contract.
        """
        if self._build.get("natspec"):
            _print_natspec(self._build["natspec"])

    def get_method(self, calldata: str) -> Optional[str]:
        sig = calldata[:10].lower()
        return self.selectors.get(sig)


class ContractContainer(_ContractBase):

    """List-like container class that holds all Contract instances of the same
    type, and is used to deploy new instances of that contract.

    Attributes:
        abi: Complete contract ABI.
        bytecode: Bytecode used to deploy the contract.
        signatures: Dictionary of {'function name': "bytes4 signature"}
        topics: Dictionary of {'event name': "bytes32 topic"}"""

    def __init__(self, project: Any, build: Dict) -> None:
        self.tx = None
        self.bytecode = build["bytecode"]
        self._contracts: List["ProjectContract"] = []
        super().__init__(project, build, project._sources)
        self.deploy = ContractConstructor(self, self._name)
        _revert_register(self)

    def __iter__(self) -> Iterator:
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
            or len(web3.eth.getCode(i.address).hex()) <= 4
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
        address: str,
        owner: Optional[AccountsType] = None,
        tx: Optional[TransactionReceiptType] = None,
    ) -> "ProjectContract":
        """Returns a contract address.

        Raises ValueError if no bytecode exists at the address.

        Args:
            address: Address string of the contract.
            owner: Default Account instance to send contract transactions from.
            tx: Transaction ID of the contract creation."""
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
        if CONFIG.network_type == "live":
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


class ContractConstructor:

    _dir_color = "bright magenta"

    def __init__(self, parent: "ContractContainer", name: str) -> None:
        self._parent = parent
        try:
            self.abi = next(i for i in parent.abi if i["type"] == "constructor")
            self.abi["name"] = "constructor"
        except Exception:
            self.abi = {"inputs": [], "name": "constructor", "type": "constructor"}
        self._name = name

    @property
    def payable(self) -> bool:
        if "payable" in self.abi:
            return self.abi["payable"]
        else:
            return self.abi["stateMutability"] == "payable"

    def __repr__(self) -> str:
        return f"<{type(self).__name__} '{self._name}.constructor({_inputs(self.abi)})'>"

    def __call__(self, *args: Tuple) -> Union["Contract", TransactionReceiptType]:
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
                "No deployer address given. You must supply a tx dict"
                " as the last argument with a 'from' field."
            )
        return tx["from"].deploy(
            self._parent,
            *args,
            amount=tx["value"],
            gas_limit=tx["gas"],
            gas_price=tx["gasPrice"],
            nonce=tx["nonce"],
            required_confs=tx["required_confs"],
        )

    @staticmethod
    def _autosuggest(obj: "ContractConstructor") -> List:
        return _contract_method_autosuggest(obj.abi["inputs"], True, obj.payable)

    def encode_input(self, *args: tuple) -> str:
        bytecode = self._parent.bytecode
        # find and replace unlinked library pointers in bytecode
        for marker in re.findall("_{1,}[^_]*_{1,}", bytecode):
            library = marker.strip("_")
            if not self._parent._project[library]:
                raise UndeployedLibrary(
                    f"Contract requires '{library}' library, but it has not been deployed yet"
                )
            address = self._parent._project[library][-1].address[-40:]
            bytecode = bytecode.replace(marker, address)

        data = format_input(self.abi, args)
        types_list = get_type_strings(self.abi["inputs"])
        return bytecode + eth_abi.encode_abi(types_list, data).hex()

    def estimate_gas(self, *args: Tuple) -> int:
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
                "Contract has no owner, you must supply a tx dict"
                " as the last argument with a 'from' field."
            )

        return tx["from"].estimate_gas(
            amount=tx["value"], gas_price=tx["gasPrice"], data=self.encode_input(*args)
        )


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
                abi = json.load(fp)
            self._add(path.stem, abi)

    def _add(self, name: str, abi: List) -> None:
        constructor = InterfaceConstructor(name, abi)
        setattr(self, name, constructor)


class InterfaceConstructor:
    """
    Constructor used to create Contract objects from a project interface.
    """

    def __init__(self, name: str, abi: List) -> None:
        self._name = name
        self.abi = abi
        self.selectors = {
            build_function_selector(i): i["name"] for i in self.abi if i["type"] == "function"
        }

    def __call__(self, address: str, owner: Optional[AccountsType] = None) -> "Contract":
        return Contract.from_abi(self._name, address, self.abi, owner)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} '{self._name}'>"


class _DeployedContractBase(_ContractBase):
    """Methods for interacting with a deployed contract.

    Each public contract method is available as a ContractCall or ContractTx
    instance, created when this class is instantiated.

    Attributes:
        bytecode: Bytecode of the deployed contract, including constructor args.
        tx: TransactionReceipt of the of the tx that deployed the contract."""

    _reverted = False

    def __init__(
        self, address: str, owner: Optional[AccountsType] = None, tx: TransactionReceiptType = None
    ) -> None:
        address = _resolve_address(address)
        self.bytecode = web3.eth.getCode(address).hex()[2:]
        if not self.bytecode:
            raise ContractNotFound(f"No contract deployed at {address}")
        self._owner = owner
        self.tx = tx
        self.address = address
        _add_deployment_topics(address, self.abi)

        fn_names = [i["name"] for i in self.abi if i["type"] == "function"]
        for abi in [i for i in self.abi if i["type"] == "function"]:
            name = f"{self._name}.{abi['name']}"
            sig = build_function_signature(abi)
            natspec: Dict = {}
            if self._build.get("natspec"):
                natspec = self._build["natspec"]["methods"].get(sig, {})

            if fn_names.count(abi["name"]) == 1:
                fn = _get_method_object(address, abi, name, owner, natspec)
                self._check_and_set(abi["name"], fn)
                continue

            # special logic to handle function overloading
            if not hasattr(self, abi["name"]):
                overloaded = OverloadedMethod(address, name, owner)
                self._check_and_set(abi["name"], overloaded)
            getattr(self, abi["name"])._add_fn(abi, natspec)

    def _check_and_set(self, name: str, obj: Any) -> None:
        if name == "balance":
            warnings.warn(
                f"'{self._name}' defines a 'balance' function, "
                f"'{self._name}.balance' is unavailable",
                BrownieEnvironmentWarning,
            )
        elif hasattr(self, name):
            raise AttributeError(f"Namespace collision: '{self._name}.{name}'")
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

    def __getattribute__(self, name: str) -> Any:
        if super().__getattribute__("_reverted"):
            raise ContractNotFound("This contract no longer exists.")
        try:
            return super().__getattribute__(name)
        except AttributeError:
            raise AttributeError(f"Contract '{self._name}' object has no attribute '{name}'")

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
        balance = web3.eth.getBalance(self.address)
        return Wei(balance)

    def _deployment_path(self) -> Optional[Path]:
        if not self._project._path or (
            CONFIG.network_type != "live" and not CONFIG.settings["dev_deployment_artifacts"]
        ):
            return None

        chainid = CONFIG.active_network["chainid"] if CONFIG.network_type == "live" else "dev"
        path = self._project._build_path.joinpath(f"deployments/{chainid}")
        path.mkdir(exist_ok=True)
        return path.joinpath(f"{self.address}.json")

    def _save_deployment(self) -> None:
        path = self._deployment_path()
        chainid = CONFIG.active_network["chainid"] if CONFIG.network_type == "live" else "dev"
        deployment_build = self._build.copy()

        deployment_build["deployment"] = {
            "address": self.address,
            "chainid": chainid,
            "blockHeight": web3.eth.blockNumber,
        }
        if path:
            self._project._add_to_deployment_map(self)
            if not path.exists():
                with path.open("w") as fp:
                    json.dump(deployment_build, fp)

    def _delete_deployment(self) -> None:
        path = self._deployment_path()
        if path:
            self._project._remove_from_deployment_map(self)
            if path.exists():
                path.unlink()


class Contract(_DeployedContractBase):
    """
    Object to interact with a deployed contract outside of a project.
    """

    def __init__(
        self, address_or_alias: str, *args: Any, owner: Optional[AccountsType] = None, **kwargs: Any
    ) -> None:
        """
        Recreate a `Contract` object from the local database.

        The init method is used to access deployments that have already previously
        been stored locally. For new deployments use `from_abi`, `from_ethpm` or
        `from_etherscan`.

        Arguments
        ---------
        address_or_alias : str
            Address or user-defined alias of the deployment.
        owner : Account, optional
            Contract owner. If set, transactions without a `from` field
            will be performed using this account.
        """
        if args or kwargs:
            warnings.warn(
                "Initializing `Contract` in this manner is deprecated."
                " Use `from_abi` or `from_ethpm` instead.",
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
                or not CONFIG.settings.get("autofetch_sources")
                or not CONFIG.active_network.get("explorer")
            ):
                if not address:
                    raise ValueError(f"Unknown alias: {address_or_alias}")
                else:
                    raise ValueError(f"Unknown contract address: {address}")
            contract = self.from_explorer(address, owner=owner, silent=True)
            build, sources = contract._build, contract._sources
            address = contract.address

        _ContractBase.__init__(self, None, build, sources)
        _DeployedContractBase.__init__(self, address, owner)

    def _deprecated_init(
        self,
        name: str,
        address: Optional[str] = None,
        abi: Optional[List] = None,
        manifest_uri: Optional[str] = None,
        owner: Optional[AccountsType] = None,
    ) -> None:
        if manifest_uri and abi:
            raise ValueError("Contract requires either abi or manifest_uri, but not both")
        if manifest_uri is not None:
            manifest = ethpm.get_manifest(manifest_uri)
            abi = manifest["contract_types"][name]["abi"]
            if address is None:
                address_list = ethpm.get_deployment_addresses(manifest, name)
                if not address_list:
                    raise ContractNotFound(
                        f"'{manifest['package_name']}' manifest does not contain"
                        f" a deployment of '{name}' on this chain"
                    )
                if len(address_list) > 1:
                    raise ValueError(
                        f"'{manifest['package_name']}' manifest contains more than one "
                        f"deployment of '{name}' on this chain, you must specify an address:"
                        f" {', '.join(address_list)}"
                    )
                address = address_list[0]
            name = manifest["contract_types"][name]["contract_name"]
        elif not address:
            raise TypeError("Address cannot be None unless creating object from manifest")

        build = {"abi": abi, "contractName": name, "type": "contract"}
        _ContractBase.__init__(self, None, build, {})  # type: ignore
        _DeployedContractBase.__init__(self, address, owner, None)

    @classmethod
    def from_abi(
        cls, name: str, address: str, abi: List, owner: Optional[AccountsType] = None
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
        build = {"abi": abi, "address": address, "contractName": name, "type": "contract"}

        self = cls.__new__(cls)
        _ContractBase.__init__(self, None, build, {})  # type: ignore
        _DeployedContractBase.__init__(self, address, owner, None)
        _add_deployment(self)
        return self

    @classmethod
    def from_ethpm(
        cls,
        name: str,
        manifest_uri: str,
        address: Optional[str] = None,
        owner: Optional[AccountsType] = None,
    ) -> "Contract":
        """
        Create a new `Contract` object from an ethPM manifest.

        Arguments
        ---------
        name : str
            Name of the contract.
        manifest_uri : str
            erc1319 registry URI where the manifest is located
        address : str optional
            Address where the contract is deployed. Only required if the
            manifest contains more than one deployment with the given name
            on the active chain.
        owner : Account, optional
            Contract owner. If set, transactions without a `from` field
            will be performed using this account.
        """
        manifest = ethpm.get_manifest(manifest_uri)

        if address is None:
            address_list = ethpm.get_deployment_addresses(manifest, name)
            if not address_list:
                raise ContractNotFound(
                    f"'{manifest['package_name']}' manifest does not contain"
                    f" a deployment of '{name}' on this chain"
                )
            if len(address_list) > 1:
                raise ValueError(
                    f"'{manifest['package_name']}' manifest contains more than one "
                    f"deployment of '{name}' on this chain, you must specify an address:"
                    f" {', '.join(address_list)}"
                )
            address = address_list[0]

        manifest["contract_types"][name]["contract_name"]
        build = {
            "abi": manifest["contract_types"][name]["abi"],
            "contractName": name,
            "natspec": manifest["contract_types"][name]["natspec"],
            "type": "contract",
        }

        self = cls.__new__(cls)
        _ContractBase.__init__(self, None, build, manifest["sources"])  # type: ignore
        _DeployedContractBase.__init__(self, address, owner)
        _add_deployment(self)
        return self

    @classmethod
    def from_explorer(
        cls,
        address: str,
        as_proxy_for: Optional[str] = None,
        owner: Optional[AccountsType] = None,
        silent: bool = False,
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

        if is_verified:
            abi = json.loads(data["result"][0]["ABI"])
            name = data["result"][0]["ContractName"]
        else:
            # if the source is not available, try to fetch only the ABI
            try:
                data_abi = _fetch_from_explorer(address, "getabi", True)
            except ValueError as exc:
                _unverified_addresses.add(address)
                raise exc
            abi = json.loads(data_abi["result"].strip())
            name = "UnknownContractName"
            warnings.warn(
                f"{address}: Was able to fetch the ABI but not the source code. "
                "Some functionality will not be available.",
                BrownieCompilerWarning,
            )

        if as_proxy_for is None and data["result"][0].get("Implementation"):
            try:
                # many proxy patterns use an `implementation()` function, so first we
                # try to determine the implementation address without trusting etherscan
                contract = cls.from_abi(name, address, abi)
                as_proxy_for = contract.implementation()
            except Exception:
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
                version = Version(compiler_str.lstrip("v")).truncate()
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

        optimizer = {
            "enabled": bool(int(data["result"][0]["OptimizationUsed"])),
            "runs": int(data["result"][0]["Runs"]),
        }
        evm_version = data["result"][0].get("EVMVersion", "Default")
        if evm_version == "Default":
            evm_version = None

        source_str = "\n".join(data["result"][0]["SourceCode"].splitlines())
        if source_str.startswith("{{"):
            # source was verified using compiler standard JSON
            input_json = json.loads(source_str[1:-1])
            sources = {k: v["content"] for k, v in input_json["sources"].items()}
            evm_version = input_json["settings"].get("evmVersion", evm_version)

            compiler.set_solc_version(str(version))
            input_json.update(
                compiler.generate_input_json(sources, optimizer=optimizer, evm_version=evm_version)
            )
            output_json = compiler.compile_from_input_json(input_json)
            build_json = compiler.generate_build_json(input_json, output_json)
        else:
            if source_str.startswith("{"):
                # source was submitted as multiple files
                sources = {k: v["content"] for k, v in json.loads(source_str).items()}
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

        build_json = build_json[name]
        if as_proxy_for is not None:
            build_json.update(abi=abi, natspec=implementation_contract._build.get("natspec"))

        if not _verify_deployed_code(
            address, build_json["deployedBytecode"], build_json["language"]
        ):
            warnings.warn(
                f"{address}: Locally compiled and on-chain bytecode do not match!",
                BrownieCompilerWarning,
            )
            del build_json["pcMap"]

        self = cls.__new__(cls)
        _ContractBase.__init__(self, None, build_json, sources)  # type: ignore
        _DeployedContractBase.__init__(self, address, owner)
        _add_deployment(self)
        return self

    def set_alias(self, alias: Optional[str]) -> None:
        """
        Apply a unique alias this object. The alias can be used to restore the
        object in future sessions.

        Arguments
        ---------
        alias: str | None
            An alias to apply. If `None`, any existing alias is removed.
        """
        if "chainid" not in CONFIG.active_network:
            raise ValueError("Cannot set aliases in a development environment")

        if alias is not None:
            if "." in alias or alias.lower().startswith("0x"):
                raise ValueError("Invalid alias")
            build, _ = _get_deployment(alias=alias)
            if build is not None:
                if build["address"] != self.address:
                    raise ValueError("Alias is already in use on another contract")
                return

        _add_deployment(self, alias)
        self._build["alias"] = alias

    @property
    def alias(self) -> Optional[str]:
        return self._build.get("alias")


class ProjectContract(_DeployedContractBase):

    """Methods for interacting with a deployed contract as part of a Brownie project."""

    def __init__(
        self,
        project: Any,
        build: Dict,
        address: str,
        owner: Optional[AccountsType] = None,
        tx: TransactionReceiptType = None,
    ) -> None:
        _ContractBase.__init__(self, project, build, project._sources)
        _DeployedContractBase.__init__(self, address, owner, tx)


class OverloadedMethod:
    def __init__(self, address: str, name: str, owner: Optional[AccountsType]):
        self._address = address
        self._name = name
        self._owner = owner
        self.methods: Dict = {}

    def _add_fn(self, abi: Dict, natspec: Dict) -> None:
        fn = _get_method_object(self._address, abi, self._name, self._owner, natspec)
        key = tuple(i["type"].replace("256", "") for i in abi["inputs"])
        self.methods[key] = fn

    def _get_fn_from_args(self, args: Tuple) -> "_ContractMethod":
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

    def __getitem__(self, key: Union[Tuple, str]) -> "_ContractMethod":
        if isinstance(key, str):
            key = tuple(i.strip() for i in key.split(","))

        key = tuple(i.replace("256", "") for i in key)
        return self.methods[key]

    def __repr__(self) -> str:
        return f"<OverloadedMethod '{self._name}'>"

    def __len__(self) -> int:
        return len(self.methods)

    def __call__(self, *args: Tuple) -> Any:
        fn = self._get_fn_from_args(args)
        return fn(*args)  # type: ignore

    def call(self, *args: Tuple, block_identifier: Union[int, str, bytes] = None) -> Any:
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

        Returns
        -------
            Contract method return value(s).
        """
        fn = self._get_fn_from_args(args)
        return fn.call(*args, block_identifier=block_identifier)

    def transact(self, *args: Tuple) -> TransactionReceiptType:
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

    def encode_input(self, *args: Tuple) -> Any:
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


class _ContractMethod:

    _dir_color = "bright magenta"

    def __init__(
        self,
        address: str,
        abi: Dict,
        name: str,
        owner: Optional[AccountsType],
        natspec: Optional[Dict] = None,
    ) -> None:
        self._address = address
        self._name = name
        self.abi = abi
        self._owner = owner
        self.signature = build_function_selector(abi)
        self._input_sig = build_function_signature(abi)
        self.natspec = natspec or {}

    def __repr__(self) -> str:
        pay = "payable " if self.payable else ""
        return f"<{type(self).__name__} {pay}'{self.abi['name']}({_inputs(self.abi)})'>"

    @property
    def payable(self) -> bool:
        if "payable" in self.abi:
            return self.abi["payable"]
        else:
            return self.abi["stateMutability"] == "payable"

    @staticmethod
    def _autosuggest(obj: "_ContractMethod") -> List:
        # this is a staticmethod to be compatible with `_call_suggest` and `_transact_suggest`
        return _contract_method_autosuggest(
            obj.abi["inputs"], isinstance(obj, ContractTx), obj.payable
        )

    def info(self) -> None:
        """
        Display NatSpec documentation for this method.
        """
        print(f"{self.abi['name']}({_inputs(self.abi)})")
        _print_natspec(self.natspec)

    def call(self, *args: Tuple, block_identifier: Union[int, str, bytes] = None) -> Any:
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

        Returns
        -------
            Contract method return value(s).
        """

        args, tx = _get_tx(self._owner, args)
        if tx["from"]:
            tx["from"] = str(tx["from"])
        del tx["required_confs"]
        tx.update({"to": self._address, "data": self.encode_input(*args)})

        try:
            data = web3.eth.call({k: v for k, v in tx.items() if v}, block_identifier)
        except ValueError as e:
            raise VirtualMachineError(e) from None

        if HexBytes(data)[:4].hex() == "0x08c379a0":
            revert_str = eth_abi.decode_abi(["string"], HexBytes(data)[4:])[0]
            raise ValueError(f"Call reverted: {revert_str}")
        if self.abi["outputs"] and not data:
            raise ValueError("No data was returned - the call likely reverted")

        return self.decode_output(data)

    def transact(self, *args: Tuple) -> TransactionReceiptType:
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
                "Contract has no owner, you must supply a tx dict"
                " as the last argument with a 'from' field."
            )

        return tx["from"].transfer(
            self._address,
            tx["value"],
            gas_limit=tx["gas"],
            gas_buffer=tx["gas_buffer"],
            gas_price=tx["gasPrice"],
            nonce=tx["nonce"],
            required_confs=tx["required_confs"],
            data=self.encode_input(*args),
        )

    def decode_input(self, hexstr: str) -> List:
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
        types_list = get_type_strings(self.abi["inputs"])
        result = eth_abi.decode_abi(types_list, HexBytes(hexstr)[4:])
        return format_input(self.abi, result)

    def encode_input(self, *args: Tuple) -> str:
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
        data = format_input(self.abi, args)
        types_list = get_type_strings(self.abi["inputs"])
        return self.signature + eth_abi.encode_abi(types_list, data).hex()

    def decode_output(self, hexstr: str) -> Tuple:
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
        types_list = get_type_strings(self.abi["outputs"])
        result = eth_abi.decode_abi(types_list, HexBytes(hexstr))
        result = format_output(self.abi, result)
        if len(result) == 1:
            result = result[0]
        return result

    def estimate_gas(self, *args: Tuple) -> int:
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
                "Contract has no owner, you must supply a tx dict"
                " as the last argument with a 'from' field."
            )

        return tx["from"].estimate_gas(
            to=self._address,
            amount=tx["value"],
            gas_price=tx["gasPrice"],
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

    def __call__(self, *args: Tuple) -> TransactionReceiptType:
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

        return self.transact(*args)


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

    def __call__(self, *args: Tuple, block_identifier: Union[int, str, bytes] = None) -> Any:
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

        Returns
        -------
            Contract method return value(s).
        """

        if not CONFIG.argv["always_transact"] or block_identifier is not None:
            return self.call(*args, block_identifier=block_identifier)

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


def _get_tx(owner: Optional[AccountsType], args: Tuple) -> Tuple:
    # set / remove default sender
    if owner is None:
        owner = accounts.default
    default_owner = CONFIG.active_network["settings"]["default_contract_owner"]
    if CONFIG.mode == "test" and default_owner is False:
        owner = None

    # seperate contract inputs from tx dict and set default tx values
    tx = {
        "from": owner,
        "value": 0,
        "gas": None,
        "gas_buffer": None,
        "gasPrice": None,
        "nonce": None,
        "required_confs": 1,
    }
    if args and isinstance(args[-1], dict):
        tx.update(args[-1])
        args = args[:-1]
        for key, target in [("amount", "value"), ("gas_limit", "gas"), ("gas_price", "gasPrice")]:
            if key in tx:
                tx[target] = tx[key]

    # enable the magic of ganache's `evm_unlockUnknownAccount`
    if isinstance(tx["from"], str):
        tx["from"] = accounts.at(tx["from"], force=True)
    elif isinstance(tx["from"], Contract):
        tx["from"] = accounts.at(tx["from"].address, force=True)

    return args, tx


def _get_method_object(
    address: str, abi: Dict, name: str, owner: Optional[AccountsType], natspec: Dict
) -> Union["ContractCall", "ContractTx"]:

    if "constant" in abi:
        constant = abi["constant"]
    else:
        constant = abi["stateMutability"] in ("view", "pure")

    if constant:
        return ContractCall(address, abi, name, owner, natspec)
    return ContractTx(address, abi, name, owner, natspec)


def _inputs(abi: Dict) -> str:
    types_list = get_type_strings(abi["inputs"], {"fixed168x10": "decimal"})
    params = zip([i["name"] for i in abi["inputs"]], types_list)
    return ", ".join(
        f"{i[1]}{color('bright blue')}{' '+i[0] if i[0] else ''}{color}" for i in params
    )


def _verify_deployed_code(address: str, expected_bytecode: str, language: str) -> bool:
    actual_bytecode = web3.eth.getCode(address).hex()[2:]
    expected_bytecode = remove_0x_prefix(expected_bytecode)  # type: ignore

    if expected_bytecode.startswith("730000000000000000000000000000000000000000"):
        # special case for Solidity libraries
        return (
            actual_bytecode.startswith(f"73{address[2:].lower()}")
            and actual_bytecode[42:] == expected_bytecode[42:]
        )

    if "_" in expected_bytecode:
        for marker in re.findall("_{1,}[^_]*_{1,}", expected_bytecode):
            idx = expected_bytecode.index(marker)
            actual_bytecode = actual_bytecode[:idx] + actual_bytecode[idx + 40 :]
            expected_bytecode = expected_bytecode[:idx] + expected_bytecode[idx + 40 :]

    if language == "Solidity":
        # do not include metadata in comparison
        idx = -(int(actual_bytecode[-4:], 16) + 2) * 2
        actual_bytecode = actual_bytecode[:idx]
        idx = -(int(expected_bytecode[-4:], 16) + 2) * 2
        expected_bytecode = expected_bytecode[:idx]

    return actual_bytecode == expected_bytecode


def _print_natspec(natspec: Dict) -> None:
    wrapper = TextWrapper(initial_indent=f"  {color('bright magenta')}")
    for key in [i for i in ("title", "notice", "author", "details") if i in natspec]:
        wrapper.subsequent_indent = " " * (len(key) + 4)
        print(wrapper.fill(f"@{key} {color}{natspec[key]}"))

    for key, value in natspec.get("params", {}).items():
        wrapper.subsequent_indent = " " * 9
        print(wrapper.fill(f"@param {color('bright blue')}{key}{color} {value}"))

    if "return" in natspec:
        wrapper.subsequent_indent = " " * 10
        print(wrapper.fill(f"@return {color}{natspec['return']}"))

    for key in sorted(natspec.get("returns", [])):
        wrapper.subsequent_indent = " " * 10
        print(wrapper.fill(f"@return {color}{natspec['returns'][key]}"))

    print()


def _fetch_from_explorer(address: str, action: str, silent: bool) -> Dict:
    url = CONFIG.active_network.get("explorer")
    if url is None:
        raise ValueError("Explorer API not set for this network")

    if address in _unverified_addresses:
        raise ValueError(f"Source for {address} has not been verified")

    params: Dict = {"module": "contract", "action": action, "address": address}
    if "etherscan" in url:
        if os.getenv("ETHERSCAN_TOKEN"):
            params["apiKey"] = os.getenv("ETHERSCAN_TOKEN")
        elif not silent:
            warnings.warn(
                "No Etherscan API token set. You may experience issues with rate limiting. "
                "Visit https://etherscan.io/register to obtain a token, and then store it "
                "as the environment variable $ETHERSCAN_TOKEN",
                BrownieEnvironmentWarning,
            )

    if not silent:
        print(
            f"Fetching source of {color('bright blue')}{address}{color} "
            f"from {color('bright blue')}{urlparse(url).netloc}{color}..."
        )

    response = requests.get(url, params=params, headers=REQUEST_HEADERS)
    if response.status_code != 200:
        raise ConnectionError(f"Status {response.status_code} when querying {url}: {response.text}")
    data = response.json()
    if int(data["status"]) != 1:
        raise ValueError(f"Failed to retrieve data from API: {data['result']}")

    return data


# console auto-completion logic


def _call_autosuggest(method: Any) -> List:
    # since methods are not unique for each object, we use `__reduce__`
    # to locate the specific object so we can access the correct ABI
    method = method.__reduce__()[1][0]
    return _contract_method_autosuggest(method.abi["inputs"], False, False)


def _transact_autosuggest(method: Any) -> List:
    method = method.__reduce__()[1][0]
    return _contract_method_autosuggest(method.abi["inputs"], True, method.payable)


# assign the autosuggest functionality to various methods
ContractConstructor.encode_input.__dict__["_autosuggest"] = _call_autosuggest
_ContractMethod.call.__dict__["_autosuggest"] = _call_autosuggest
_ContractMethod.encode_input.__dict__["_autosuggest"] = _call_autosuggest

ContractConstructor.estimate_gas.__dict__["_autosuggest"] = _transact_autosuggest
_ContractMethod.estimate_gas.__dict__["_autosuggest"] = _transact_autosuggest
_ContractMethod.transact.__dict__["_autosuggest"] = _transact_autosuggest


def _contract_method_autosuggest(args: List, is_transaction: bool, is_payable: bool) -> List:
    types_list = get_type_strings(args, {"fixed168x10": "decimal"})
    params = zip([i["name"] for i in args], types_list)

    if not is_transaction:
        tx_hint: List = []
    elif is_payable:
        tx_hint = [" {'from': Account", " 'value': Wei}"]
    else:
        tx_hint = [" {'from': Account}"]

    return [f" {i[1]}{' '+i[0] if i[0] else ''}" for i in params] + tx_hint
