#!/usr/bin/python3

from typing import Iterable, List, Union, Dict, Any, Optional, Tuple, Callable
import re

import eth_abi
from eth_hash.auto import keccak
from hexbytes import HexBytes

from brownie.cli.utils import color
from .event import get_topics
from . import history
from .rpc import Rpc
from .web3 import Web3
from brownie.convert import format_input, format_output, to_address, Wei
from brownie.exceptions import (
    ContractExists,
    ContractNotFound,
    UndeployedLibrary,
    VirtualMachineError
)
from brownie._config import ARGV, CONFIG

from brownie.typing import TransactionReceiptType, AccountsType

rpc = Rpc()
web3 = Web3()


class _ContractBase:

    _dir_color = "contract"

    def __init__(self, project: Any, build: Any, name: str, abi: Any) -> None:
        self._project = project
        self._build = build
        self._name = name
        self.abi = abi
        self.topics = get_topics(abi)
        self.signatures = dict((
            i['name'],
            _signature(i)
        ) for i in abi if i['type'] == "function")

    def get_method(self, calldata: str) -> Optional[Iterable]:
        sig = calldata[:10].lower()
        return next((k for k, v in self.signatures.items() if v == sig), None)


class ContractContainer(_ContractBase):

    '''List-like container class that holds all Contract instances of the same
    type, and is used to deploy new instances of that contract.

    Attributes:
        abi: Complete contract ABI.
        bytecode: Bytecode used to deploy the contract.
        signatures: Dictionary of {'function name': "bytes4 signature"}
        topics: Dictionary of {'event name': "bytes32 topic"}'''

    def __init__(self, project: Any, build: Dict) -> None:
        self.tx = None
        self.bytecode = build['bytecode']
        self._contracts: List = []
        super().__init__(project, build, build['contractName'], build['abi'])
        self.deploy = ContractConstructor(self, self._name)
        rpc._revert_register(self)

    def __iter__(self) -> Iterable:
        return iter(self._contracts)

    def __getitem__(self, i: Any) -> Any:
        return self._contracts[i]

    def __delitem__(self, key: Any) -> None:
        item = self._contracts[key]
        history._remove_contract(item)
        self._contracts.remove(item)

    def __len__(self) -> int:
        return len(self._contracts)

    def __repr__(self) -> str:
        return str(self._contracts)

    def _reset(self) -> None:
        for contract in self._contracts:
            history._remove_contract(contract)
            contract._reverted = True
        self._contracts.clear()

    def _revert(self, height: int) -> None:
        reverted = [
            i for i in self._contracts if
            (i.tx and i.tx.block_number > height) or
            len(web3.eth.getCode(i.address).hex()) <= 4
        ]
        for contract in reverted:
            history._remove_contract(contract)
            self._contracts.remove(contract)
            contract._reverted = True

    def remove(self, contract: str) -> None:
        '''Removes a contract from the container.

        Args:
            contract: Contract instance of address string of the contract.'''
        if contract not in self._contracts:
            raise TypeError("Object is not in container.")
        self._contracts.remove(contract)
        history._remove_contract(contract)

    def at(
            self,
            address: str,
            owner: Optional[AccountsType] = None,
            tx: Any = None) -> 'ProjectContract':
        '''Returns a contract address.

        Raises ValueError if no bytecode exists at the address.

        Args:
            address: Address string of the contract.
            owner: Default Account instance to send contract transactions from.
            tx: Transaction ID of the contract creation.'''
        contract = history.find_contract(address)
        if contract:
            if contract._name == self._name and contract._project == self._project:
                return contract
            raise ContractExists(
                f"'{contract._name}' declared at {address} in project '{contract._project._name}'"
            )
        contract = ProjectContract(self._project, self._build, address, owner, tx)
        self._contracts.append(contract)
        return contract

    def _add_from_tx(self, tx: TransactionReceiptType) -> None:
        tx._confirmed.wait()
        self.at(tx.contract_address, tx.sender, tx)


class ContractConstructor:

    _dir_color = "contract_method"

    def __init__(self, parent: Any, name: str) -> None:
        self._parent = parent
        try:
            self.abi = next(i for i in parent.abi if i['type'] == "constructor")
            self.abi['name'] = "constructor"
        except Exception:
            self.abi = {
                'inputs': [],
                'name': "constructor",
                'type': "constructor"
            }
        self._name = name

    def __repr__(self) -> str:
        return f"<{type(self).__name__} object '{self._name}.constructor({_inputs(self.abi)})'>"

    def __call__(self, *args: Tuple) -> Union['Contract', TransactionReceiptType]:
        '''Deploys a contract.

        Args:
            *args: Constructor arguments. The last argument MUST be a dictionary
                   of transaction values containing at minimum a 'from' key to
                   specify which account to deploy this contract from.

        Returns:
            * Contract instance if the transaction confirms
            * TransactionReceipt if the transaction is pending or reverts'''
        args, tx = _get_tx(None, args)
        if not tx['from']:
            raise AttributeError(
                "Contract has no owner, you must supply a tx dict"
                " with a 'from' field as the last argument."
            )
        return tx['from'].deploy(
            self._parent,
            *args,
            amount=tx['value'],
            gas_limit=tx['gas'],
            gas_price=tx['gasPrice']
        )

    def encode_abi(self, *args: tuple) -> str:
        bytecode = self._parent.bytecode
        # find and replace unlinked library pointers in bytecode
        for marker in re.findall('_{1,}[^_]*_{1,}', bytecode):
            library = marker.strip('_')
            if not self._parent._project[library]:
                raise UndeployedLibrary(
                    f"Contract requires '{library}' library, but it has not been deployed yet"
                )
            address = self._parent._project[library][-1].address[-40:]
            bytecode = bytecode.replace(marker, address)

        data = format_input(self.abi, args)
        types = [i[1] for i in _params(self.abi['inputs'])]
        return bytecode + eth_abi.encode_abi(types, data).hex()


class _DeployedContractBase(_ContractBase):
    '''Methods for interacting with a deployed contract.

    Each public contract method is available as a ContractCall or ContractTx
    instance, created when this class is instantiated.

    Attributes:
        bytecode: Bytecode of the deployed contract, including constructor args.
        tx: TransactionReceipt of the of the tx that deployed the contract.'''

    _reverted = False

    def __init__(self, address: str, owner: Any = None, tx: TransactionReceiptType = None) -> None:
        address = to_address(address)
        self.bytecode = web3.eth.getCode(address).hex()[2:]
        if not self.bytecode:
            raise ContractNotFound(f"No contract deployed at {address}")
        self._owner = owner
        self.tx = tx
        self.address = address
        fn_names = [i['name'] for i in self.abi if i['type'] == "function"]
        for abi in [i for i in self.abi if i['type'] == "function"]:
            name = f"{self._name}.{abi['name']}"
            if fn_names.count(abi['name']) == 1:
                self._check_and_set(abi['name'], _get_method_object(address, abi, name, owner))
                continue
            if not hasattr(self, abi['name']):
                self._check_and_set(abi['name'], OverloadedMethod(address, name, owner))
            key = ",".join(i['type'] for i in abi['inputs']).replace('256', '')
            getattr(self, abi['name']).methods[key] = _get_method_object(address, abi, name, owner)

    def _check_and_set(self, name: str, obj: Any) -> None:
        if hasattr(self, name):
            raise AttributeError(f"Namespace collision: '{self._name}.{name}'")
        setattr(self, name, obj)

    def __hash__(self) -> int:
        return hash(f"{self._name}{self.address}{self._project}")

    def __str__(self) -> str:
        return self.address

    def __repr__(self) -> str:
        return f"<{self._name} Contract object '{color['string']}{self.address}{color}'>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _DeployedContractBase):
            return self.address == other.address and self.bytecode == other.bytecode
        if isinstance(other, str):
            try:
                address = to_address(other)
                return address == self.address
            except ValueError:
                return False
        return super().__eq__(other)

    def __getattribute__(self, name: str) -> Any:
        if super().__getattribute__('_reverted'):
            raise ContractNotFound("This contract no longer exists.")
        return super().__getattribute__(name)

    def balance(self) -> int:
        '''Returns the current ether balance of the contract, in wei.'''
        balance = web3.eth.getBalance(self.address)
        return Wei(balance)


class Contract(_DeployedContractBase):

    def __init__(self, address: Any, name: str, abi: Any, owner: AccountsType = None) -> None:
        _ContractBase.__init__(self, None, None, name, abi)
        _DeployedContractBase.__init__(self, address, owner, None)
        contract = history.find_contract(address)
        if not contract:
            return
        if isinstance(contract, ProjectContract):
            raise ContractExists(
                f"'{contract._name}' declared at {address} in project '{contract._project._name}'"
            )
        if contract.bytecode != self.bytecode:
            contract._reverted = True


class ProjectContract(_DeployedContractBase):

    '''Methods for interacting with a deployed contract as part of a Brownie project.'''

    def __init__(
            self,
            project: '_DeployedContractBase',
            build: Any,
            address: str,
            # Not really optional. Helps to satisfy None default in ContractContainer at method
            # Could use some refactoring
            owner: Optional[AccountsType],
            tx: TransactionReceiptType = None) -> None:
        _ContractBase.__init__(self, project, build, build['contractName'], build['abi'])
        _DeployedContractBase.__init__(self, address, owner, tx)
        history._add_contract(self)


class OverloadedMethod:

    def __init__(self, address: str, name: str, owner: Any):
        self._address = address
        self._name = name
        self._owner = owner
        self.methods: Dict = {}

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, tuple):
            key = ",".join(key)
        key = key.replace("256", "").replace(", ", ",")
        return self.methods[key]

    def __repr__(self) -> str:
        return f"<OverloadedMethod object '{self._name}'>"

    def __len__(self) -> int:
        return len(self.methods)


class _ContractMethod:

    _dir_color = "contract_method"

    def __init__(self, address: str, abi: Any, name: str, owner: Optional[AccountsType]) -> None:
        self._address = address
        self._name = name
        self.abi = abi
        self._owner = owner
        self.signature = _signature(abi)

    def __repr__(self) -> str:
        pay = "payable " if self.abi['stateMutability'] == "payable" else ""
        return f"<{type(self).__name__} {pay}object '{self.abi['name']}({_inputs(self.abi)})'>"

    def call(self, *args: Tuple) -> Any:
        '''Calls the contract method without broadcasting a transaction.

        Args:
            *args: Contract method inputs. You can optionally provide a
                   dictionary of transaction properties as the last arg.

        Returns:
            Contract method return value(s).'''
        args, tx = _get_tx(self._owner, args)
        if tx['from']:
            tx['from'] = str(tx['from'])
        tx.update({'to': self._address, 'data': self.encode_abi(*args)})
        try:
            data = web3.eth.call(dict((k, v) for k, v in tx.items() if v))
        except ValueError as e:
            raise VirtualMachineError(e) from None
        return self.decode_abi(data)

    def transact(self, *args: Tuple) -> TransactionReceiptType:
        '''Broadcasts a transaction that calls this contract method.

        Args:
            *args: Contract method inputs. You can optionally provide a
                   dictionary of transaction properties as the last arg.

        Returns:
            TransactionReceipt instance.'''
        args, tx = _get_tx(self._owner, args)
        if not tx['from']:
            raise AttributeError(
                "No deployer address given. You must supply a tx dict"
                " with a 'from' field as the last argument."
            )
        return tx['from'].transfer(
            self._address,
            tx['value'],
            gas_limit=tx['gas'],
            gas_price=tx['gasPrice'],
            data=self.encode_abi(*args)
        )

    def encode_abi(self, *args: Tuple) -> str:
        '''Returns encoded ABI data to call the method with the given arguments.

        Args:
            *args: Contract method inputs

        Returns:
            Hexstring of encoded ABI data.'''
        data = format_input(self.abi, args)
        types = [i[1] for i in _params(self.abi['inputs'])]
        return self.signature + eth_abi.encode_abi(types, data).hex()

    def decode_abi(self, hexstr: str) -> Tuple:
        '''Decodes hexstring data returned by this method.

        Args:
            hexstr: Hexstring of returned call data

        Returns: Decoded values.'''
        types = [i[1] for i in _params(self.abi['outputs'])]
        result = eth_abi.decode_abi(types, HexBytes(hexstr))
        result = format_output(self.abi, result)
        if len(result) == 1:
            result = result[0]
        return result


class ContractTx(_ContractMethod):

    '''A public payable or non-payable contract method.

    Args:
        abi: Contract ABI specific to this method.
        signature: Bytes4 method signature.'''

    def __init__(self, address: str, abi: Any, name: str, owner: Optional[AccountsType]) -> None:
        if ARGV['cli'] == "test" and CONFIG['pytest']['default_contract_owner'] is False:
            owner = None
        super().__init__(address, abi, name, owner)

    def __call__(self, *args: Tuple) -> Any:
        '''Broadcasts a transaction that calls this contract method.

        Args:
            *args: Contract method inputs. You can optionally provide a
                   dictionary of transaction properties as the last arg.

        Returns:
            TransactionReceipt instance.'''
        return self.transact(*args)


class ContractCall(_ContractMethod):

    '''A public view or pure contract method.

    Args:
        abi: Contract ABI specific to this method.
        signature: Bytes4 method signature.'''

    def __call__(self, *args: Tuple) -> Callable:
        '''Calls the contract method without broadcasting a transaction.

        Args:
            *args: Contract method inputs. You can optionally provide a
                   dictionary of transaction properties as the last arg.

        Returns:
            Contract method return value(s).'''
        if not ARGV['always_transact']:
            return self.call(*args)
        rpc._internal_snap()
        args, tx = _get_tx(self._owner, args)
        tx['gas_price'] = 0
        try:
            tx = self.transact(*args, tx)
            return tx.return_value
        finally:
            rpc._internal_revert()


def _get_tx(owner: Optional[AccountsType], args: Any) -> Tuple:
    # seperate contract inputs from tx dict and set default tx values
    tx = {'from': owner, 'value': 0, 'gas': None, 'gasPrice': None}
    if args and isinstance(args[-1], dict):
        tx.update(args[-1])
        args = args[:-1]
        for key, target in [
            ('amount', 'value'),
            ('gas_limit', 'gas'),
            ('gas_price', 'gasPrice')
        ]:
            if key in tx:
                tx[target] = tx[key]
    return args, tx


def _get_method_object(
        address: str,
        abi: Any,
        name: str,
        owner: Optional[AccountsType]) -> Union['ContractCall', 'ContractTx']:
    if abi['stateMutability'] in ('view', 'pure'):
        return ContractCall(address, abi, name, owner)
    return ContractTx(address, abi, name, owner)


def _params(abi_params: List) -> Any:
    types = []
    for i in abi_params:
        if i['type'] != "tuple":
            types.append((i['name'], i['type']))
            continue
        types.append((i['name'], f"({','.join(x[1] for x in _params(i['components']))})"))
    return types


def _inputs(abi: Any) -> str:
    params = _params(abi['inputs'])
    return ", ".join(f"{i[1]}{' '+i[0] if i[0] else ''}" for i in params)


def _signature(abi: Any) -> str:
    types = [i[1] for i in _params(abi['inputs'])]
    key = f"{abi['name']}({','.join(types)})".encode()
    return "0x" + keccak(key).hex()[:8]
