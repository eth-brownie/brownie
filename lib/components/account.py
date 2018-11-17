#!/usr/bin/python3

import json

from lib.components.eth import web3,TransactionReceipt

class VMError(Exception):

    def __init__(self,e):
        super().__init__(eval(str(e))['message'])


class Accounts(list):

    def __init__(self, accounts):
        super().__init__([Account(i) for i in accounts])

    def add(self, priv_key):
        w3account = web3.eth.account.privateKeyToAccount(priv_key)
        account = LocalAccount(w3account.address, w3account, priv_key)
        #account._acct = w3account
        #account._priv_key = priv_key
        self.append(account)
        return account
    
    def at(self, address):
        address = web3.toChecksumAddress(address)
        try:
            return next(i for i in self if i == address)
        except StopIteration:
            print("ERROR: No account exists for {}".format(address))


class _AccountBase(str):

    def __init__(self, addr):
        self.address = addr
        self.nonce = web3.eth.getTransactionCount(self.address)

    def __repr__(self):
        return "<Account object '{}'>".format(self.address)

    def __str__(self):
        return self.__repr__()

    def balance(self):
        return web3.eth.getBalance(self.address)

    def deploy(self, contract, *args):
        return contract.deploy(self, *args)
    
    def estimate_gas(self, to, amount, data=""):
        return web3.eth.estimateGas({
            'from':self.address,
            'to':to,
            'data':data,
            'value':int(amount)
            })


class Account(_AccountBase):

    def transfer(self, to, amount, gas_price=None):
        try:
            txid = web3.eth.sendTransaction({
                'from': self.address,
                'to': to,
                'value': int(amount),
                'gasPrice': gas_price or web3.eth.gasPrice,
                'gas': self.estimate_gas(to, amount)
                })
            self.nonce += 1
            return TransactionReceipt(txid)
        except ValueError as e:
            raise VMError(e)

    def _contract_call(self, fn, args, tx):
        tx['from'] = self.address
        try: txid = fn(*args).transact(tx)
        except ValueError as e:
            raise VMError(e)
        self.nonce += 1
        return TransactionReceipt(txid)


class LocalAccount(_AccountBase):

    def __new__(cls, address, *args):
        return super().__new__(cls, address)

    def __init__(self, address, account, priv_key):
        self._acct = account
        self._priv_key = priv_key
        super().__init__(address)

    def transfer(self, to, amount, gas_price=None):
        try:
            signed_tx = self._acct.signTransaction({
                'from': self.address,
                'nonce': self.nonce,
                'gasPrice': gas_price or web3.eth.gasPrice,
                'gas': self.estimate_gas(to, amount),
                'to': to,
                'value': int(amount),
                'data': ""
                }).rawTransaction
            txid = web3.eth.sendRawTransaction(signed_tx)
            self.nonce += 1
            return TransactionReceipt(txid)
        except ValueError as e:
            raise VMError(e)

    def _contract_call(self, fn, args, tx):
        try:
            tx.update({
                'from':self.address,
                'nonce':self.nonce,
                'gasPrice': web3.eth.gasPrice,
                'gas': fn(*args).estimateGas({'from': self.address}),
                })
            raw = fn(*args).buildTransaction(tx)
            txid = web3.eth.sendRawTransaction(
                self._acct.signTransaction(raw).rawTransaction)
            self.nonce += 1
            return TransactionReceipt(txid)
        except ValueError as e:
            raise VMError(e)
