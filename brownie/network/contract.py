#!/usr/bin/python3

import re

import eth_abi
from eth_hash.auto import keccak

from brownie.cli.utils import color
from .event import get_topics
from .history import _ContractHistory
from .rpc import Rpc
from .web3 import Web3
from brownie.types import KwargTuple
from brownie.types.convert import format_input, format_output, to_address
from brownie.exceptions import VirtualMachineError
from brownie._config import ARGV, CONFIG

_contracts = _ContractHistory()
rpc = Rpc()
web3 = Web3()


class _ContractBase:

    _dir_color = "contract"

    def __init__(self, build):
        self._build = build
        self.abi = build['abi']
        self._name = build['contractName']
        names = [i['name'] for i in self.abi if i['type'] == "function"]
        duplicates = set(i for i in names if names.count(i) > 1)
        if duplicates:
            raise AttributeError("Ambiguous contract functions in {}: {}".format(
                self._name, ",".join(duplicates)))
        self.topics = get_topics(self.abi)
        self.signatures = dict((
            i['name'],
            "0x"+keccak("{}({})".format(
                i['name'], ",".join(x['type'] for x in i['inputs'])
            ).encode()).hex()[:8]
        ) for i in self.abi if i['type'] == "function")

    def get_method(self, calldata):
        return next(
            (k for k, v in self.signatures.items() if v == calldata[:10].lower()),
            None
        )


class ContractContainer(_ContractBase):

    '''List-like container class that holds all Contract instances of the same
    type, and is used to deploy new instances of that contract.

    Attributes:
        abi: Complete contract ABI.
        bytecode: Bytecode used to deploy the contract.
        signatures: Dictionary of {'function name': "bytes4 signature"}
        topics: Dictionary of {'event name': "bytes32 topic"}'''

    def __init__(self, build):
        self.tx = None
        self.bytecode = build['bytecode']
        super().__init__(build)
        self.deploy = ContractConstructor(self, self._name)

    def __iter__(self):
        return iter(_contracts.list(self._name))

    def __getitem__(self, i):
        return _contracts.list(self._name)[i]

    def __delitem__(self, key):
        item = _contracts.list(self._name)[key]
        _contracts.remove(item)

    def __len__(self):
        return len(_contracts.list(self._name))

    def __repr__(self):
        return "<ContractContainer object '{1[string]}{0._name}{1}'>".format(self, color)

    def _console_repr(self):
        return str(_contracts.list(self._name))

    def remove(self, contract):
        '''Removes a contract from the container.

        Args:
            contract: Contract instance of address string of the contract.'''
        if type(contract) is not Contract or contract._name != self._name:
            raise TypeError("Object is not in container.")
        _contracts.remove(contract)

    def at(self, address, owner=None, tx=None):
        '''Returns a contract address.

        Raises ValueError if no bytecode exists at the address.

        Args:
            address: Address string of the contract.
            owner: Default Account instance to send contract transactions from.
            tx: Transaction ID of the contract creation.'''
        address = to_address(address)
        contract = _contracts.find(address)
        if contract:
            if contract._name != self._name:
                raise ValueError("Contract '{}' already declared at {}".format(
                    contract._name, address
                ))
            return contract
        if web3.eth.getCode(address).hex() == "0x":
            raise ValueError("No contract deployed at {}".format(address))
        contract = Contract(address, self._build, owner, tx)
        _contracts.add(contract)
        return contract


class ContractConstructor:

    _dir_color = "contract_method"

    def __init__(self, parent, name):
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

    def __repr__(self):
        return "<{} object '{}.constructor({})'>".format(
            type(self).__name__,
            self._name,
            ", ".join("{0[type]}{1}{0[name]}".format(
                i,
                " " if i['name'] else ""
            ) for i in self.abi['inputs'])
        )

    def __call__(self, account, *args):
        '''Deploys a contract.

        Args:
            account: Account instance to deploy the contract from.
            *args: Constructor arguments. The last argument may optionally be
                   a dictionary of transaction values.

        Returns:
            * Contract instance if the transaction confirms
            * TransactionReceipt if the transaction is pending or reverts'''
        args, tx = _get_tx(account, args)
        return account.deploy(
            self._parent,
            *args,
            amount=tx['value'],
            gas_limit=tx['gas'],
            gas_price=tx['gasPrice'],
            callback=self._callback
        )

    def _callback(self, tx):
        # ensures the Contract instance is added to the container if the user
        # presses CTRL-C while deployment is still pending
        if tx.status == 1:
            tx.contract_address = self._parent.at(tx.contract_address, tx.sender, tx)

    def encode_abi(self, *args):
        bytecode = self._parent.bytecode
        # find and replace unlinked library pointers in bytecode
        for marker in re.findall('_{1,}[^_]*_{1,}', bytecode):
            library = marker.strip('_')
            if not _contracts.list(library):
                raise IndexError(
                    "Contract requires '{}' library".format(library) +
                    " but it has not been deployed yet"
                )
            address = _contracts.list(library)[-1].address[-40:]
            bytecode = bytecode.replace(marker, address)

        data = format_input(self.abi, args)
        types = [i['type'] for i in self.abi['inputs']]
        return bytecode + eth_abi.encode_abi(types, data).hex()


class Contract(_ContractBase):

    '''Methods for interacting with a deployed contract.

    Each public contract method is available as a ContractCall or ContractTx
    instance, created when this class is instantiated.

    Attributes:
        bytecode: Bytecode of the deployed contract, including constructor args.
        tx: TransactionReceipt of the of the tx that deployed the contract.'''

    def __init__(self, address, build, owner, tx=None):
        super().__init__(build)
        self.tx = tx
        self.bytecode = web3.eth.getCode(address).hex()[2:]
        self._owner = owner
        self.address = address
        for i in [i for i in self.abi if i['type'] == "function"]:
            if hasattr(self, i['name']):
                raise AttributeError(
                    "Namespace collision: '{}.{}'".format(self._name, i['name'])
                )
            name = "{}.{}".format(self._name, i['name'])
            if i['stateMutability'] in ('view', 'pure'):
                setattr(self, i['name'], ContractCall(address, i, name, owner))
            else:
                setattr(self, i['name'], ContractTx(address, i, name, owner))

    def __repr__(self):
        return "<{0._name} Contract object '{1[string]}{0.address}{1}'>".format(self, color)

    def __str__(self):
        return self.address

    def __eq__(self, other):
        if type(other) is str:
            try:
                address = to_address(other)
                return address == self.address
            except ValueError:
                return False
        return super().__eq__(other)

    def balance(self):
        '''Returns the current ether balance of the contract, in wei.'''
        return web3.eth.getBalance(self.address)


class _ContractMethod:

    _dir_color = "contract_method"

    def __init__(self, address, abi, name, owner):
        self._address = address
        self._name = name
        self.abi = abi
        self._owner = owner
        self.signature = "0x"+keccak("{}({})".format(
            abi['name'],
            ",".join(i['type'] for i in abi['inputs'])
            ).encode()).hex()[:8]

    def __repr__(self):
        return "<{} {}object '{}({})'>".format(
            type(self).__name__,
            "payable " if self.abi['stateMutability'] == "payable" else "",
            self.abi['name'],
            ", ".join("{0[type]}{1}{0[name]}".format(
                i,
                " " if i['name'] else ""
            ) for i in self.abi['inputs'])
        )

    def call(self, *args):
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
            raise VirtualMachineError(e)
        result = eth_abi.decode_abi([i['type'] for i in self.abi['outputs']], data)
        if len(result) == 1:
            return format_output(result[0])
        return KwargTuple(result, self.abi)

    def transact(self, *args):
        '''Broadcasts a transaction that calls this contract method.

        Args:
            *args: Contract method inputs. You can optionally provide a
                   dictionary of transaction properties as the last arg.

        Returns:
            TransactionReceipt instance.'''
        args, tx = _get_tx(self._owner, args)
        if not tx['from']:
            raise AttributeError(
                "Contract has no owner, you must supply a tx dict"
                " with a 'from' field as the last argument."
            )
        rpc._internal_clear()
        return tx['from'].transfer(
            self._address,
            tx['value'],
            gas_limit=tx['gas'],
            gas_price=tx['gasPrice'],
            data=self.encode_abi(*args)
        )

    def encode_abi(self, *args):
        '''Returns encoded ABI data to call the method with the given arguments.

        Args:
            *args: Contract method inputs

        Returns:
            Hexstring of encoded ABI data.'''
        data = format_input(self.abi, args)
        types = [i['type'] for i in self.abi['inputs']]
        return self.signature + eth_abi.encode_abi(types, data).hex()


class ContractTx(_ContractMethod):

    '''A public payable or non-payable contract method.

    Args:
        abi: Contract ABI specific to this method.
        signature: Bytes4 method signature.'''

    def __init__(self, fn, abi, name, owner):
        if (
            ARGV['cli'] != "console" and not
            CONFIG['test']['default_contract_owner']
        ):
            owner = None
        super().__init__(fn, abi, name, owner)

    def __call__(self, *args):
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

    def __call__(self, *args):
        '''Calls the contract method without broadcasting a transaction.

        Args:
            *args: Contract method inputs. You can optionally provide a
                   dictionary of transaction properties as the last arg.

        Returns:
            Contract method return value(s).'''
        if ARGV['always_transact']:
            rpc._internal_snap()
            tx = self.transact(*args, {'gas_price': 0})
            if tx.modified_state:
                rpc._internal_revert()
            return tx.return_value
        return self.call(*args)


def _get_tx(owner, args):
    # seperate contract inputs from tx dict and set default tx values
    tx = {'from': owner, 'value': 0, 'gas': None, 'gasPrice': None}
    if args and type(args[-1]) is dict:
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
