#!/usr/bin/python3

import json
import os
import re
import warnings
from pathlib import Path
from textwrap import TextWrapper
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

import eth_abi
import requests
from eth_utils import remove_0x_prefix
from hexbytes import HexBytes
from semantic_version import Version

from brownie._config import CONFIG
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
from brownie.project import ethpm
from brownie.project.compiler import compile_and_format
from brownie.typing import AccountsType, TransactionReceiptType
from brownie.utils import color

from . import accounts, rpc
from .event import _get_topics
from .rpc import _revert_register
from .state import _add_contract, _add_deployment, _find_contract, _get_deployment, _remove_contract
from .web3 import _resolve_address, web3

__tracebackhide__ = True

_unverified_addresses: Set = set()


class _ContractBase:

    _dir_color = "bright magenta"

    def __init__(self, project: Any, build: Dict, sources: Dict) -> None:
        self._project = project
        self._build = build.copy()
        self._sources = sources
        self.topics = _get_topics(self.abi)
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
        return next((k for k, v in self.signatures.items() if v == sig), None)


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
        return str(self._contracts)

    def _reset(self) -> None:
        for contract in self._contracts:
            _remove_contract(contract)
            contract._reverted = True
        self._contracts.clear()

    def _revert(self, height: int) -> None:
        reverted = [
            i
            for i in self._contracts
            if (i.tx and i.tx.block_number > height) or len(web3.eth.getCode(i.address).hex()) <= 4
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
        if tx.status:
            self.at(tx.contract_address, tx.sender, tx)


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
                " with a 'from' field as the last argument."
            )
        return tx["from"].deploy(
            self._parent, *args, amount=tx["value"], gas_limit=tx["gas"], gas_price=tx["gasPrice"]
        )

    def _autosuggest(self) -> List:
        return _contract_method_autosuggest(self)

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


class InterfaceContainer:
    """
    Container class that provides access to interfaces within a project.
    """

    def __init__(self, project: Any) -> None:
        self._project = project

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

            if not hasattr(self, abi["name"]):
                overloaded = OverloadedMethod(address, name, owner)
                self._check_and_set(abi["name"], overloaded)

            key = ",".join(i["type"] for i in abi["inputs"]).replace("256", "")
            fn = _get_method_object(address, abi, name, owner, natspec)
            getattr(self, abi["name"]).methods[key] = fn

    def _check_and_set(self, name: str, obj: Any) -> None:
        if hasattr(self, name):
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
        return super().__getattribute__(name)

    def balance(self) -> Wei:
        """Returns the current ether balance of the contract, in wei."""
        balance = web3.eth.getBalance(self.address)
        return Wei(balance)

    def _deployment_path(self) -> Optional[Path]:
        if CONFIG.network_type != "live" or not self._project._path:
            return None
        chainid = CONFIG.active_network["chainid"]
        path = self._project._path.joinpath(f"build/deployments/{chainid}")
        path.mkdir(exist_ok=True)
        return path.joinpath(f"{self.address}.json")

    def _save_deployment(self) -> None:
        path = self._deployment_path()
        if path and not path.exists():
            with path.open("w") as fp:
                json.dump(self._build, fp)

    def _delete_deployment(self) -> None:
        path = self._deployment_path()
        if path and path.exists():
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
            and NatSpec of `as_proxy_for`.
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
                data = _fetch_from_explorer(address, "getabi", True)
            except ValueError as exc:
                _unverified_addresses.add(address)
                raise exc
            abi = json.loads(data["result"].strip())
            name = "UnknownContractName"
            warnings.warn(
                f"{address}: Was able to fetch the ABI but not the source code. "
                "Some functionality will not be available.",
                BrownieCompilerWarning,
            )

        # if this is a proxy, fetch information for the implementation contract
        if as_proxy_for is not None:
            implementation_contract = Contract.from_explorer(as_proxy_for)
            abi = implementation_contract._build["abi"]

        if not is_verified:
            return cls.from_abi(name, address, abi, owner)

        try:
            version = Version(data["result"][0]["CompilerVersion"].lstrip("v")).truncate()
        except Exception:
            version = Version("0.0.0")
        if version < Version("0.4.22"):
            if not silent:
                warnings.warn(
                    f"{address}: target compiler '{data['result'][0]['CompilerVersion']}' is "
                    "unsupported by Brownie. Some functionality will not be available.",
                    BrownieCompilerWarning,
                )
            return cls.from_abi(name, address, abi, owner)

        sources = {f"{name}-flattened.sol": data["result"][0]["SourceCode"]}
        optimizer = {
            "enabled": bool(int(data["result"][0]["OptimizationUsed"])),
            "runs": int(data["result"][0]["Runs"]),
        }
        build = compile_and_format(sources, solc_version=str(version), optimizer=optimizer)
        build = build[name]
        if as_proxy_for is not None:
            build.update(abi=abi, natspec=implementation_contract._build["natspec"])

        if not _verify_deployed_code(address, build["deployedBytecode"], build["language"]):
            warnings.warn(
                f"{address}: Locally compiled and on-chain bytecode do not match!",
                BrownieCompilerWarning,
            )
            del build["pcMap"]

        self = cls.__new__(cls)
        _ContractBase.__init__(self, None, build, sources)  # type: ignore
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

    def __getitem__(self, key: Union[Tuple, str]) -> "_ContractMethod":
        if isinstance(key, tuple):
            key = ",".join(key)
        key = key.replace("256", "").replace(", ", ",")
        return self.methods[key]

    def __repr__(self) -> str:
        return f"<OverloadedMethod '{self._name}'>"

    def __len__(self) -> int:
        return len(self.methods)


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

    def _autosuggest(self) -> List:
        return _contract_method_autosuggest(self)

    def info(self) -> None:
        """
        Display NatSpec documentation for this method.
        """
        print(f"{self.abi['name']}({_inputs(self.abi)})")
        _print_natspec(self.natspec)

    def call(self, *args: Tuple) -> Any:
        """Calls the contract method without broadcasting a transaction.

        Args:
            *args: Contract method inputs. You can optionally provide a
                   dictionary of transaction properties as the last arg.

        Returns:
            Contract method return value(s)."""

        args, tx = _get_tx(self._owner, args)
        if tx["from"]:
            tx["from"] = str(tx["from"])
        tx.update({"to": self._address, "data": self.encode_input(*args)})
        try:
            data = web3.eth.call(dict((k, v) for k, v in tx.items() if v))
        except ValueError as e:
            raise VirtualMachineError(e) from None
        return self.decode_output(data)

    def transact(self, *args: Tuple) -> TransactionReceiptType:
        """Broadcasts a transaction that calls this contract method.

        Args:
            *args: Contract method inputs. You can optionally provide a
                   dictionary of transaction properties as the last arg.

        Returns:
            TransactionReceipt instance."""

        args, tx = _get_tx(self._owner, args)
        if not tx["from"]:
            raise AttributeError(
                "Contract has no owner, you must supply a tx dict"
                " with a 'from' field as the last argument."
            )
        return tx["from"].transfer(
            self._address,
            tx["value"],
            gas_limit=tx["gas"],
            gas_price=tx["gasPrice"],
            data=self.encode_input(*args),
        )

    def encode_input(self, *args: Tuple) -> str:
        """Returns encoded ABI data to call the method with the given arguments.

        Args:
            *args: Contract method inputs

        Returns:
            Hexstring of encoded ABI data."""
        data = format_input(self.abi, args)
        types_list = get_type_strings(self.abi["inputs"])
        return self.signature + eth_abi.encode_abi(types_list, data).hex()

    def decode_output(self, hexstr: str) -> Tuple:
        """Decodes hexstring data returned by this method.

        Args:
            hexstr: Hexstring of returned call data

        Returns: Decoded values."""
        types_list = get_type_strings(self.abi["outputs"])
        result = eth_abi.decode_abi(types_list, HexBytes(hexstr))
        result = format_output(self.abi, result)
        if len(result) == 1:
            result = result[0]
        return result


class ContractTx(_ContractMethod):

    """A public payable or non-payable contract method.

    Args:
        abi: Contract ABI specific to this method.
        signature: Bytes4 method signature."""

    def __call__(self, *args: Tuple) -> TransactionReceiptType:
        """Broadcasts a transaction that calls this contract method.

        Args:
            *args: Contract method inputs. You can optionally provide a
                   dictionary of transaction properties as the last arg.

        Returns:
            TransactionReceipt instance."""

        return self.transact(*args)


class ContractCall(_ContractMethod):

    """A public view or pure contract method.

    Args:
        abi: Contract ABI specific to this method.
        signature: Bytes4 method signature."""

    def __call__(self, *args: Tuple) -> Callable:
        """Calls the contract method without broadcasting a transaction.

        Args:
            *args: Contract method inputs. You can optionally provide a
                   dictionary of transaction properties as the last arg.

        Returns:
            Contract method return value(s)."""

        if not CONFIG.argv["always_transact"]:
            return self.call(*args)
        args, tx = _get_tx(self._owner, args)
        tx.update({"gas_price": 0, "from": self._owner or accounts[0]})
        try:
            tx = self.transact(*args, tx)
            return tx.return_value
        finally:
            rpc.undo()


def _get_tx(owner: Optional[AccountsType], args: Tuple) -> Tuple:
    # set / remove default sender
    if owner is None:
        owner = accounts.default
    default_owner = CONFIG.active_network["settings"]["default_contract_owner"]
    if CONFIG.mode == "test" and default_owner is False:
        owner = None

    # seperate contract inputs from tx dict and set default tx values
    tx = {"from": owner, "value": 0, "gas": None, "gasPrice": None}
    if args and isinstance(args[-1], dict):
        tx.update(args[-1])
        args = args[:-1]
        for key, target in [("amount", "value"), ("gas_limit", "gas"), ("gas_price", "gasPrice")]:
            if key in tx:
                tx[target] = tx[key]
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


def _contract_method_autosuggest(method: Any) -> List:
    types_list = get_type_strings(method.abi["inputs"], {"fixed168x10": "decimal"})
    params = zip([i["name"] for i in method.abi["inputs"]], types_list)

    if isinstance(method, ContractCall):
        tx_hint: List = []
    elif method.payable:
        tx_hint = [" {'from': Account", " 'value': Wei}"]
    else:
        tx_hint = [" {'from': Account}"]

    return [f" {i[1]}{' '+i[0] if i[0] else ''}" for i in params] + tx_hint


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
    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise ConnectionError(f"Status {response.status_code} when querying {url}: {response.text}")
    data = response.json()
    if int(data["status"]) != 1:
        raise ValueError(f"Failed to retrieve data from API: {data['result']}")

    return data
