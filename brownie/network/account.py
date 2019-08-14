#!/usr/bin/python3

from getpass import getpass
from hexbytes import HexBytes
import os
from pathlib import Path
import json

from eth_hash.auto import keccak
import eth_keys

from brownie.cli.utils import color
from brownie.exceptions import VirtualMachineError, UnknownAccount, IncompatibleEVMVersion
from brownie.network.transaction import TransactionReceipt
from .rpc import Rpc
from .web3 import Web3
from brownie.convert import to_address, Wei
from brownie._singleton import _Singleton
from brownie._config import CONFIG

web3 = Web3()
rpc = Rpc()


class Accounts(metaclass=_Singleton):

    '''List-like container that holds all of the available Account instances.'''

    def __init__(self):
        self._accounts = []
        # prevent private keys from being stored in read history
        self.add.__dict__['_private'] = True
        rpc._revert_register(self)
        self._reset()

    def _reset(self):
        self._accounts.clear()
        try:
            self._accounts = [Account(i) for i in web3.eth.accounts]
        except Exception:
            pass

    def _revert(self):
        for i in self._accounts:
            i.nonce = web3.eth.getTransactionCount(str(i))

    def __contains__(self, address):
        try:
            address = to_address(address)
            return address in self._accounts
        except ValueError:
            return False

    def __repr__(self):
        return str(self._accounts)

    def __iter__(self):
        return iter(self._accounts)

    def __getitem__(self, key):
        return self._accounts[key]

    def __delitem__(self, key):
        del self._accounts[key]

    def __len__(self):
        return len(self._accounts)

    def add(self, priv_key=None):
        '''Creates a new ``LocalAccount`` instance and appends it to the container.

        Args:
            priv_key: Private key of the account. If none is given, one is
                      randomly generated.

        Returns:
            Account instance.'''
        if not priv_key:
            priv_key = "0x" + keccak(os.urandom(8192)).hex()
        w3account = web3.eth.account.from_key(priv_key)
        if w3account.address in self._accounts:
            return self.at(w3account.address)
        account = LocalAccount(w3account.address, w3account, priv_key)
        self._accounts.append(account)
        return account

    def load(self, filename=None):
        '''Loads a local account from a keystore file.

        Args:
            filename: Keystore filename. If none is given, returns a list of
                      available keystores.

        Returns:
            Account instance.'''
        project_path = CONFIG['brownie_folder'].joinpath("data/accounts")
        if not filename:
            return [i.stem for i in project_path.glob('*.json')]
        filename = str(filename)
        if not filename.endswith(".json"):
            filename += ".json"
        json_file = Path(filename).expanduser()
        if not json_file.exists():
            json_file = project_path.joinpath(filename)
            if not json_file.exists():
                raise FileNotFoundError(f"Cannot find {json_file}")
        with json_file.open() as fp:
            priv_key = web3.eth.account.decrypt(
                json.load(fp),
                getpass("Enter the password for this account: ")
            )
        return self.add(priv_key)

    def at(self, address):
        '''Retrieves an Account instance from the address string. Raises
        ValueError if the account cannot be found.

        Args:
            address: string of the account address.

        Returns:
            Account instance.
        '''
        address = to_address(address)
        try:
            return next(i for i in self._accounts if i == address)
        except StopIteration:
            raise UnknownAccount(f"No account exists for {address}")

    def remove(self, address):
        '''Removes an account instance from the container.

        Args:
            address: Account instance or address string of account to remove.'''
        address = to_address(address)
        try:
            self._accounts.remove(address)
        except ValueError:
            raise UnknownAccount(f"No account exists for {address}")

    def clear(self):
        '''Empties the container.'''
        self._accounts.clear()


class _AccountBase:

    '''Base class for Account and LocalAccount'''

    def __init__(self, addr):
        self.address = addr
        self.nonce = web3.eth.getTransactionCount(self.address)

    def __hash__(self):
        return hash(self.address)

    def __repr__(self):
        return f"'{color['string']}{self.address}{color}'"

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

    def _gas_limit(self, to, amount, data=""):
        if type(CONFIG['active_network']['gas_limit']) is int:
            return CONFIG['active_network']['gas_limit']
        return self.estimate_gas(to, amount, data)

    def _gas_price(self):
        return CONFIG['active_network']['gas_price'] or web3.eth.gasPrice

    def _check_for_revert(self, tx):
        if (
            'broadcast_reverting_tx' not in CONFIG['active_network'] or
            CONFIG['active_network']['broadcast_reverting_tx']
        ):
            return
        try:
            web3.eth.call(dict((k, v) for k, v in tx.items() if v))
        except ValueError as e:
            raise VirtualMachineError(e) from None

    def balance(self):
        '''Returns the current balance at the address, in wei.'''
        balance = web3.eth.getBalance(self.address)
        return Wei(balance)

    def deploy(self, contract, *args, amount=None, gas_limit=None, gas_price=None, callback=None):
        '''Deploys a contract.

        Args:
            contract: ContractContainer instance.
            *args: Constructor arguments. The last argument may optionally be
                   a dictionary of transaction values.

        Kwargs:
            amount: Amount of ether to send with transaction, in wei.
            gas_limit: Gas limit of the transaction.
            gas_price: Gas price of the transaction.
            callback: Callback function to attach to TransactionReceipt.

        Returns:
            * Contract instance if the transaction confirms
            * TransactionReceipt if the transaction is pending or reverts'''
        evm = contract._build['compiler']['evm_version']
        if rpc.is_active() and not rpc.evm_compatible(evm):
            raise IncompatibleEVMVersion(
                f"Local RPC using '{rpc.evm_version()}' but contract was compiled for '{evm}'"
            )
        data = contract.deploy.encode_abi(*args)
        try:
            txid = self._transact({
                'from': self.address,
                'value': Wei(amount),
                'nonce': self.nonce,
                'gasPrice': Wei(gas_price) or self._gas_price(),
                'gas': Wei(gas_limit) or self._gas_limit("", amount, data),
                'data': HexBytes(data)
            })
            revert = None
        except ValueError as e:
            txid, revert = _raise_or_return_tx(e)
        self.nonce += 1
        tx = TransactionReceipt(
            txid,
            self,
            name=contract._name + ".constructor",
            callback=callback,
            revert=revert
        )
        if tx.status != 1:
            return tx
        tx.contract_address = contract.at(tx.contract_address, self, tx)
        return tx.contract_address

    def estimate_gas(self, to, amount, data=""):
        '''Estimates the gas cost for a transaction. Raises VirtualMachineError
        if the transaction would revert.

        Args:
            to: Account instance or address string of transaction recipient.
            amount: Amount of ether to send in wei.
            data: Transaction data hexstring.

        Returns:
            Estimated gas value in wei.'''
        return web3.eth.estimateGas({
            'from': self.address,
            'to': str(to),
            'value': Wei(amount),
            'data': HexBytes(data)
        })

    def transfer(self, to, amount, gas_limit=None, gas_price=None, data=""):
        '''Transfers ether from this account.

        Args:
            to: Account instance or address string to transfer to.
            amount: Amount of ether to send, in wei.

        Kwargs:
            gas_limit: Gas limit of the transaction.
            gas_price: Gas price of the transaction.
            data: Hexstring of data to include in transaction.

        Returns:
            TransactionReceipt object'''
        try:
            txid = self._transact({
                'from': self.address,
                'to': str(to),
                'value': Wei(amount),
                'nonce': self.nonce,
                'gasPrice': Wei(gas_price) if gas_price is not None else self._gas_price(),
                'gas': Wei(gas_limit) or self._gas_limit(to, amount, data),
                'data': HexBytes(data)
            })
            revert = None
        except ValueError as e:
            txid, revert = _raise_or_return_tx(e)
        self.nonce += 1
        return TransactionReceipt(txid, self, revert=revert)


class Account(_AccountBase):

    '''Class for interacting with an Ethereum account.

    Attributes:
        address: Public address of the account.
        nonce: Current nonce of the account.'''

    def __repr__(self):
        return f"<Account object '{color['string']}{self.address}{color}'>"

    def _transact(self, tx):
        self._check_for_revert(tx)
        return web3.eth.sendTransaction(tx)


class LocalAccount(_AccountBase):

    '''Class for interacting with an Ethereum account.

    Attributes:
        address: Public address of the account.
        nonce: Current nonce of the account.
        private_key: Account private key.
        public_key: Account public key.'''

    def __init__(self, address, account, priv_key):
        self._acct = account
        self.private_key = priv_key
        self.public_key = eth_keys.keys.PrivateKey(HexBytes(priv_key)).public_key
        super().__init__(address)

    def __repr__(self):
        return f"<LocalAccount object '{color['string']}{self.address}{color}'>"

    def save(self, filename, overwrite=False):
        '''Encrypts the private key and saves it in a keystore json.

        Attributes:
            filename: path to keystore file. If no folder is given, saved in
                      brownie/data/accounts
            overwrite: if True, will overwrite an existing file.

        Returns the absolute path to the keystore file as a string.
        '''
        path = CONFIG['brownie_folder'].joinpath('data/accounts')
        path.mkdir(exist_ok=True)
        filename = str(filename)
        if not filename.endswith(".json"):
            filename += ".json"
        if not any(i in r"\/" for i in filename):
            json_file = path.joinpath(filename).resolve()
        else:
            json_file = Path(filename).expanduser().resolve()
        if not overwrite and json_file.exists():
            raise FileExistsError("Account with this identifier already exists")
        encrypted = web3.eth.account.encrypt(
            self.private_key,
            getpass("Enter the password to encrypt this account with: ")
        )
        with json_file.open('w') as fp:
            json.dump(encrypted, fp)
        return str(json_file)

    def _transact(self, tx):
        self._check_for_revert(tx)
        signed_tx = self._acct.signTransaction(tx).rawTransaction
        return web3.eth.sendRawTransaction(signed_tx)


def _raise_or_return_tx(exc):
    try:
        data = eval(str(exc))['data']
        txid = next(i for i in data.keys() if i[:2] == "0x")
        reason = data[txid]['reason'] if 'reason' in data[txid] else None
        pc = data[txid]['program_counter'] - 1
        error = data[txid]['error']
        return txid, [reason, pc, error]
    except SyntaxError:
        raise exc
    except Exception:
        raise VirtualMachineError(exc) from None
