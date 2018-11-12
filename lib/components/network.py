#!/usr/bin/python3

import importlib
import os
import sys
import traceback

from lib.components.config import CONFIG
from lib.components.eth import web3, COMPILED
from lib.components.account import Account
from lib.components.contract import ContractDeployer
import lib.components.check as check


class Network:

    check = check

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
        if not os.path.exists('deployments/{}.py'.format(name)):
            print("ERROR: Cannot find deployments/{}.py".format(name))
            return
        module = importlib.import_module("deployments."+name)
        module.__dict__.update(self._network_dict)
        print("Running deployment script '{}'...".format(name))
        try:
            module.deploy()
            print("Deployment of '{}' was successful.".format(name))
        except Exception as e:
            if CONFIG['logging']['exc']>=2:
                print("".join(traceback.format_tb(sys.exc_info()[2])))
            print("ERROR: Deployment of '{}' failed from unhandled {}: {}".format(
                name, type(e).__name__, e))

    def reset(self, network=None):
        if network:
            if network not in CONFIG['networks']:
                print("ERROR: Network '{}' is not defined in config.json".format(network))
            CONFIG['default_network'] = network
        for i in [i for i in self._module.__dict__ if i not in self._clean_dict]:
            del self._module.__dict__[i]
        web3._reset()
        self.__init__(self._module)

    def logging(self, value = None):
        if type(value) is not int or not 0<=value<=2:
            print("Logging options:\n 0 - Quiet\n 1 - Normal\n 2 - Verbose")
        else:
            CONFIG['logging'] = int(value)
            print("Logging level set to {}.".format(value))