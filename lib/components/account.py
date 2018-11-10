#!/usr/bin/python3

from lib.components.eth import web3


class _AccountBase(str):

    def __init__(self, addr):
        self.address = addr
        self.nonce = web3.eth.getTransactionCount(self.address)

    def __repr__(self):
        return "<Account object '{}'>".format(self.address)

    def __str__(self):
        return self.address

    def balance(self):
        return web3.eth.getBalance(self.address)

    def deploy(self, contract, *args):
        return contract.deploy(self, *args)

    def revert(self, cmd, *args):
        if cmd not in ['transfer', 'deploy']:
            raise AttributeError("Unknown command")
        try:
            getattr(self, cmd)(*args)
            return False
        except ValueError:
            return True
    
    def estimate_gas(self, to, amount, data=""):
        return web3.eth.estimateGas({
            'from':self.address,
            'to':to,
            'data':data,
            'value':int(amount)
            })


class Account(_AccountBase):

    def transfer(self, to, amount, gas_price=None):
        txid = web3.eth.sendTransaction({
            'from': self.address,
            'to': to,
            'value': int(amount),
            'gasPrice': gas_price or web3.eth.gasPrice,
            'gas': self.estimate_gas(to, amount)
            })
        self.nonce += 1
        return web3.toHex(txid)

    def _contract_call(self, fn, args, tx):
        tx['from'] = self.address
        txid = fn(*args).transact(tx)
        self.nonce += 1
        return web3.eth.waitForTransactionReceipt(txid)


class LocalAccount(_AccountBase):

    def transfer(self, to, amount, gas_price=None):
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
        return web3.toHex(txid)

    def _contract_call(self, fn, args, tx):
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
        return web3.eth.waitForTransactionReceipt(txid)

