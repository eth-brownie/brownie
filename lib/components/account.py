#!/usr/bin/python3

import eth_keys
from hexbytes import HexBytes
import json
import os

from lib.components.transaction import TransactionReceipt, raise_or_return_tx
from lib.components.eth import web3, wei
from lib.services.bip44 import HDPrivateKey, HDKey
from lib.services import config, color
CONFIG = config.CONFIG


class Accounts:

    def __init__(self, accounts):
        self._accounts = [Account(i) for i in accounts]

    def __contains__(self, address):
        try:
            address = web3.toChecksumAddress(address)
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
    
    def _check_nonce(self):
        for i in self._accounts:
            i.nonce = web3.eth.getTransactionCount(str(i))

    def add(self, priv_key = None):
        if not priv_key:
            priv_key=web3.sha3(os.urandom(8192)).hex()
        w3account = web3.eth.account.privateKeyToAccount(priv_key)
        if w3account.address in self._accounts:
            return self.at(w3account.address)
        account = LocalAccount(w3account.address, w3account, priv_key)
        self._accounts.append(account)
        return account

    def at(self, address):
        try:
            address = web3.toChecksumAddress(address)
        except ValueError:
            raise ValueError("{} is not a valid address".format(address))
        try:
            return next(i for i in self._accounts if i == address)
        except StopIteration:
            raise ValueError("No account exists for {}".format(address))

    def mnemonic(self, phrase, count=10):
        master_key = HDPrivateKey.master_key_from_mnemonic(phrase)
        acct_priv_key = HDKey.from_path(master_key, "m/44'/60'/0'")[-1]
        for i in range(count):
            priv_key = HDKey.from_path(acct_priv_key, "0/{}".format(i))[-1]
            self.add(priv_key._key.to_hex())

    def remove(self, address):
        self._accounts.remove(address)

    def clear(self):
        self._accounts.clear()


class _AccountBase:

    def __init__(self, addr):
        self.address = addr
        self.nonce = web3.eth.getTransactionCount(self.address)

    def __repr__(self):
        return "<Account object '{0[string]}{1}{0}'>".format(color, self.address)

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
        return web3.eth.getBalance(self.address)

    def deploy(self, contract, *args, **kwargs):
        return contract.deploy(self, *args, **kwargs)
    
    def estimate_gas(self, to, amount, data=""):
        return web3.eth.estimateGas({
            'from':self.address,
            'to':str(to),
            'data':data,
            'value':wei(amount)
        })

    def _gas_limit(self, to, amount, data=""):
        if type(CONFIG['active_network']['gas_limit']) is int:
            return CONFIG['active_network']['gas_limit']
        return self.estimate_gas(to, amount, data)

    def _gas_price(self):
        return CONFIG['active_network']['gas_price'] or web3.eth.gasPrice


class Account(_AccountBase):

    def transfer(self, to, amount, gas_limit=None, gas_price=None):
        try:
            txid = web3.eth.sendTransaction({
                'from': self.address,
                'to': str(to),
                'value': wei(amount),
                'gasPrice': wei(gas_price) or self._gas_price(),
                'gas': wei(gas_limit) or self._gas_limit(to, amount)
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

    def __init__(self, address, account, priv_key):
        self._acct = account
        self.private_key = priv_key
        self.public_key = eth_keys.keys.PrivateKey(HexBytes(priv_key)).public_key
        super().__init__(address)

    def transfer(self, to, amount, gas_limit=None, gas_price=None):
        try:
            signed_tx = self._acct.signTransaction({
                'from': self.address,
                'nonce': self.nonce,
                'gasPrice': wei(gas_price) or self._gas_price(),
                'gas': wei(gas_limit) or self._gas_limit(to, amount),
                'to': to,
                'value': wei(amount),
                'data': ""
            }).rawTransaction
            txid = web3.eth.sendRawTransaction(signed_tx)
        except ValueError as e:
            txid = raise_or_return_tx(e)
        self.nonce += 1
        return TransactionReceipt(txid, self)

    def _contract_tx(self, fn, args, tx, name, callback=None):
        try:
            tx.update({
                'from':self.address,
                'nonce':self.nonce,
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
