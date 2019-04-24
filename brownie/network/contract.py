#!/usr/bin/python3

import re

import eth_abi
from eth_hash.auto import keccak
from eth_utils import to_checksum_address

from brownie.cli.utils import color
from brownie.exceptions import VirtualMachineError
from brownie.network.event import get_topics
from brownie.network.history import history
from brownie.network.web3 import web3
from brownie.types import KwargTuple
from brownie.types.convert import format_to_abi, format_output, wei

import brownie._config as config
CONFIG = config.CONFIG


class _ContractBase:

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
        # convert pcMap to dict to speed transaction stack traces
        if type(build['pcMap']) is list:
            build['pcMap'] = dict((i.pop('pc'), i) for i in build['pcMap'])
        super().__init__(build)
        self.deploy = ContractConstructor(self, self._name)

    def __iter__(self):
        return iter(history.get_contracts(self._name).values())

    def __getitem__(self, i):
        return list(history.get_contracts(self._name).values())[i]

    def __delitem__(self, key):
        del history.get_contracts(self._name)[self[key].address]

    def __len__(self):
        return len(history.get_contracts(self._name))

    def __repr__(self):
        return "<ContractContainer object '{1[string]}{0._name}{1}'>".format(self, color)

    def _console_repr(self):
        return str(list(history.get_contracts(self._name).values()))

    def remove(self, contract):
        '''Removes a contract from the container.

        Args:
            contract: Contract instance of address string of the contract.'''
        del history.get_contracts(self._name)[str(contract)]

    def at(self, address, owner=None, tx=None):
        '''Returns a contract address.

        Raises ValueError if no bytecode exists at the address.

        Args:
            address: Address string of the contract.
            owner: Default Account instance to send contract transactions from.
            tx: Transaction ID of the contract creation.'''
        address = to_checksum_address(str(address))
        if address in history.get_contracts(self._name):
            return history.get_contracts(self._name)[address]
        contract = history.find_contract(address)
        if contract:
            raise ValueError("Contract '{}' already declared at {}".format(
                contract._name, address
            ))
        if web3.eth.getCode(address).hex() == "0x":
            raise ValueError("No contract deployed at {}".format(address))
        contract = Contract(address, self._build, owner, tx)
        history.get_contracts(self._name)[address] = contract
        return history.get_contracts(self._name)[address]


class ContractConstructor:

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
        if self.abi:
            args = ",".join(i['type'] for i in self.abi['inputs'])
        else:
            args = ""
        return "<{} object '{}.constructor({})'>".format(
            type(self).__name__, self._name, args
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
        bytecode = self._parent.bytecode
        if '_' in bytecode:
            # find and replace unlinked library pointers in bytecode
            for marker in re.findall('_{1,}[^_]*_{1,}', bytecode):
                contract = marker.strip('_')
                if contract not in history._contracts:
                    raise NameError(
                        "Contract requires unknown library '{}'".format(contract)
                    )
                elif not history.get_contracts(contract):
                    raise IndexError(
                        "Contract requires '{}' library".format(contract) +
                        " but it has not been deployed yet"
                    )
                bytecode = bytecode.replace(
                    marker,
                    list(history.get_contracts(contract).values())[-1].address[-40:]
                )
        contract = web3.eth.contract(abi=[self.abi], bytecode=bytecode)
        args, tx = _get_tx(account, args)
        tx = account._contract_tx(
            contract.constructor,
            format_to_abi(self.abi, args),
            tx,
            self._name+".constructor",
            self._callback
        )
        if tx.status == 1:
            tx.contract_address = self._parent.at(tx.contract_address)
            return tx.contract_address
        return tx

    def _callback(self, tx):
        # ensures the Contract instance is added to the container if the user
        # presses CTRL-C while deployment is still pending
        if tx.status == 1:
            tx.contract_address = self._parent.at(tx.contract_address, tx.sender, tx)


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
        self._contract = web3.eth.contract(address=address, abi=self.abi)
        for i in [i for i in self.abi if i['type'] == "function"]:
            if hasattr(self, i['name']):
                raise AttributeError(
                    "Namespace collision: '{}.{}'".format(self._name, i['name'])
                )
            fn = getattr(self._contract.functions, i['name'])
            name = "{}.{}".format(self._name, i['name'])
            if i['stateMutability'] in ('view', 'pure'):
                setattr(self, i['name'], ContractCall(fn, i, name, owner))
            else:
                setattr(self, i['name'], ContractTx(fn, i, name, owner))

    def __repr__(self):
        return "<{0._name} Contract object '{1[string]}{0.address}{1}'>".format(self, color)

    def __str__(self):
        return self._contract.address

    def __getattr__(self, name):
        return getattr(self._contract, name)

    def __eq__(self, other):
        if type(other) is str:
            try:
                address = to_checksum_address(other)
                return address == self.address
            except ValueError:
                return False
        return super().__eq__(other)

    def balance(self):
        '''Returns the current ether balance of the contract, in wei.'''
        return web3.eth.getBalance(self._contract.address)


class _ContractMethod:

    def __init__(self, fn, abi, name, owner):
        self._fn = fn
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
        else:
            del tx['from']
        try:
            result = self._fn(*format_to_abi(self.abi, args)).call(tx)
        except ValueError as e:
            raise VirtualMachineError(e)

        if type(result) is not list or len(result) == 1:
            return format_output(result)
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
        return tx['from']._contract_tx(
            self._fn,
            format_to_abi(self.abi, args),
            tx,
            self._name
        )

    def encode_abi(self, *args):
        '''Returns encoded ABI data to call the method with the given arguments.

        Args:
            *args: Contract method inputs

        Returns:
            Hexstring of encoded ABI data.'''
        data = format_to_abi(self.abi, args)
        types = [i['type'] for i in self.abi['inputs']]
        return self.signature + eth_abi.encode_abi(types, data).hex()


class ContractTx(_ContractMethod):

    '''A public payable or non-payable contract method.

    Args:
        abi: Contract ABI specific to this method.
        signature: Bytes4 method signature.'''

    def __init__(self, fn, abi, name, owner):
        if (
            config.ARGV['cli'] != "console" and not
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
        if config.ARGV['cli'] != "console" and CONFIG['test']['always_transact']:
            tx = self.transact(*args)
            return tx.return_value
        return self.call(*args)


def _get_tx(owner, args):
    # seperate contract inputs from tx dict
    if args and type(args[-1]) is dict:
        args, tx = (args[:-1], args[-1].copy())
        if 'from' not in tx:
            tx['from'] = owner
        for key in [i for i in ('value', 'gas', 'gasPrice') if i in tx]:
            tx[key] = wei(tx[key])
    else:
        tx = {'from': owner}
    return args, tx
