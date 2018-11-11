#!/usr/bin/python3

import importlib

from lib.components.config import CONFIG
from lib.components.eth import web3, COMPILED
from lib.components.account import Account
from lib.components.contract import ContractDeployer


class Network:

    def __init__(self, module):
        self._clean_dict = list(module.__dict__)
        self._module = module
        self.accounts = [Account(i) for i in web3.eth.accounts]
        for name, interface in COMPILED.items():
            setattr(self, name.split(':')[-1], ContractDeployer(interface))
        self._network_dict = dict(
            [(i,getattr(self,i)) for i in dir(self) if i[0]!='_'] +
            [(i,getattr(web3,i)) for i in dir(web3) if i[0].islower()])
        module.__dict__.update(self._network_dict)
        print("Brownie environment is ready.")
        if hasattr(module, 'DEPLOYMENT'):
            self.run(module.DEPLOYMENT)

    def add_account(self, priv_key):
        w3account = web3.eth.account.privateKeyToAccount(priv_key)
        account = LocalAccount(w3account.address)
        account._acct = w3account
        account._priv_key = priv_key
        self.accounts.append(account)
        return account

    def run(self, name):
        module = importlib.import_module("deployments."+name)
        module.__dict__.update(self._network_dict)
        print("Running deployment script '{}'...".format(name))
        try:
            module.deploy()
            print("Deployment of '{}' was successful.".format(name))
        except Exception as e:
            print("ERROR: Deployment of '{}' failed due to {} - {}".format(
                    name, type(e).__name__, e))

    def reset(self):
        for i in [i for i in self._module.__dict__ if i not in self._clean_dict]:
            del self._module.__dict__[i]
        web3._reset()
        self.__init__(self._module)