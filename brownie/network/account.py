#!/usr/bin/python3

import eth_keys
from hexbytes import HexBytes
import os
import sys

from brownie.network.transaction import TransactionReceipt, raise_or_return_tx
from brownie.utils import color, wei
from brownie.utils.bip44 import HDPrivateKey, HDKey

import brownie._registry as _registry
import brownie.config
CONFIG = brownie.config.CONFIG

web3 = None
_registry.add(sys.modules[__name__])

class Accounts:

    '''List-like container that holds all of the available Account instances.'''

    def __init__(self):
        self._accounts = []
        # prevent mnemonics and private keys from being stored in read history
        self.add.__dict__['_private'] = True
        self.mnemonic.__dict__['_private'] = True
        _registry.add(self)

    def _notify_reset(self):
        self._accounts.clear()
        if web3:
            self._accounts = [Account(i) for i in web3.eth.accounts]

    def _notify_revert(self):
        for i in self._accounts:
            i.nonce = web3.eth.getTransactionCount(str(i))

    def __contains__(self, address):
        try:
            address = web3.toChecksumAddress(address)
            return address in self._accounts
        except ValueError:
            return False

    def _console_repr(self):
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
            Account instance.
        '''
        if not priv_key:
            priv_key = web3.sha3(os.urandom(8192)).hex()
        w3account = web3.eth.account.privateKeyToAccount(priv_key)
        if w3account.address in self._accounts:
            return self.at(w3account.address)
        account = LocalAccount(w3account.address, w3account, priv_key)
        self._accounts.append(account)
        return account

    def at(self, address):
        '''Retrieves an Account instance from the address string. Raises
        ValueError if the account cannot be found.

        Args:
            address: string of the account address.

        Returns:
            Account instance.
        '''
        try:
            address = web3.toChecksumAddress(address)
        except ValueError:
            raise ValueError("{} is not a valid address".format(address))
        try:
            return next(i for i in self._accounts if i == address)
        except StopIteration:
            raise ValueError("No account exists for {}".format(address))

    def mnemonic(self, phrase, count=10):
        '''Generates LocalAccount instances from a seed phrase based on the
        BIP44 standard.

        Args:
            phrase: Seed phrase
            count: Number of accounts to generate
        '''
        master_key = HDPrivateKey.master_key_from_mnemonic(phrase)
        acct_priv_key = HDKey.from_path(master_key, "m/44'/60'/0'")[-1]
        for i in range(count):
            priv_key = HDKey.from_path(acct_priv_key, "0/{}".format(i))[-1]
            self.add(priv_key._key.to_hex())

    def remove(self, address):
        '''Removes an account instance from the container.

        Args:
            address: Account instance or address string of account to remove.'''
        self._accounts.remove(address)

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
        return "'{0[string]}{1}{0}'".format(color, self.address)

    def __str__(self):
        return self.address

    def __eq__(self, other):
        if type(other) is str:
            try:
                address = web3.toChecksumAddress(other)
                return address == self.address
            except ValueError:
                return False
        return super().__eq__(other)

    def balance(self):
        '''Returns the current balance at the address, in wei.'''
        return web3.eth.getBalance(self.address)

    def deploy(self, contract, *args):
        '''Deploys a contract.

        Args:
            contract: ContractContainer instance.
            *args: Constructor arguments. The last argument may optionally be
                   a dictionary of transaction values.

        Returns:
            * Contract instance if the transaction confirms
            * TransactionReceipt if the transaction is pending or reverts'''
        return contract.deploy(self, *args)

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
            'data': HexBytes(data),
            'value': wei(amount)
        })

    def _gas_limit(self, to, amount, data=""):
        if type(CONFIG['active_network']['gas_limit']) is int:
            return CONFIG['active_network']['gas_limit']
        return self.estimate_gas(to, amount, data)

    def _gas_price(self):
        return CONFIG['active_network']['gas_price'] or web3.eth.gasPrice


class Account(_AccountBase):

    '''Class for interacting with an Ethereum account.

    Attributes:
        address: Public address of the account.
        nonce: Current nonce of the account.'''

    def _console_repr(self):
        return "<Account object '{0[string]}{1}{0}'>".format(color, self.address)

    def transfer(self, to, amount, gas_limit=None, gas_price=None, data=''):
        '''Transfers ether from this account.

        Args:
            to: Account instance or address string to transfer to.
            amount: Amount of ether to send, in wei.
            gas_limit: Gas limit of the transaction.
            gas_price: Gas price of the transaction.

        Returns:
            TransactionReceipt instance'''
        try:
            txid = web3.eth.sendTransaction({
                'from': self.address,
                'to': str(to),
                'value': wei(amount),
                'gasPrice': wei(gas_price) or self._gas_price(),
                'gas': wei(gas_limit) or self._gas_limit(to, amount, data),
                'data': HexBytes(data)
            })
        except ValueError as e:
            txid = raise_or_return_tx(e)
        self.nonce += 1
        return TransactionReceipt(txid, self)

    def _contract_tx(self, fn, args, tx, name, callback=None):
        tx['from'] = self.address
        if type(CONFIG['active_network']['gas_price']) is int:
            tx['gasPrice'] = CONFIG['active_network']['gas_price']
        if type(CONFIG['active_network']['gas_limit']) is int:
            tx['gas'] = CONFIG['active_network']['gas_limit']
        try:
            txid = fn(*args).transact(tx)
        except ValueError as e:
            txid = raise_or_return_tx(e)
        self.nonce += 1
        return TransactionReceipt(txid, self, name=name, callback=callback)


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

    def _console_repr(self):
        return "<LocalAccount object '{0[string]}{1}{0}'>".format(color, self.address)

    def transfer(self, to, amount, gas_limit=None, gas_price=None, data=''):
        '''Transfers ether from this account.

        Args:
            to: Account instance or address string to transfer to.
            amount: Amount of ether to send, in wei.
            gas_limit: Gas limit of the transaction.
            gas_price: Gas price of the transaction.

        Returns:
            TransactionReceipt instance'''
        try:
            signed_tx = self._acct.signTransaction({
                'from': self.address,
                'nonce': self.nonce,
                'gasPrice': wei(gas_price) or self._gas_price(),
                'gas': wei(gas_limit) or self._gas_limit(to, amount, data),
                'to': str(to),
                'value': wei(amount),
                'data': HexBytes(data)
            }).rawTransaction
            txid = web3.eth.sendRawTransaction(signed_tx)
        except ValueError as e:
            txid = raise_or_return_tx(e)
        self.nonce += 1
        return TransactionReceipt(txid, self)

    def _contract_tx(self, fn, args, tx, name, callback=None):
        try:
            tx.update({
                'from': self.address,
                'nonce': self.nonce,
                'gasPrice': self._gas_price(),
                'gas': (
                    CONFIG['active_network']['gas_limit'] or
                    fn(*args).estimateGas({'from': self.address})
                )
            })
            raw = fn(*args).buildTransaction(tx)
            txid = web3.eth.sendRawTransaction(
                self._acct.signTransaction(raw).rawTransaction
            )
        except ValueError as e:
            txid = raise_or_return_tx(e)
        self.nonce += 1
        return TransactionReceipt(txid, self, name=name, callback=callback)
