#!/usr/bin/python3

from getpass import getpass
import importlib
import json
import os
import sys
import traceback

from lib.services.fernet import FernetKey, InvalidToken
from lib.components.config import CONFIG
from lib.components.eth import web3, wei, COMPILED
from lib.components.account import Accounts, LocalAccount
from lib.components.contract import ContractDeployer
import lib.components.check as check


class Network:

    def __init__(self, module):
        self._module = module
        accounts = Accounts(web3.eth.accounts)
        self._network_dict = {
            'a': accounts,
            'accounts': accounts,
            'check': check,
            'logging': self.logging,
            'reset': self.reset,
            'run': self.run,
            'web3': web3,
            'wei': wei }
        for name, interface in COMPILED.items():
            name = name.split(':')[-1]
            if name in self._network_dict:
                raise AttributeError("Namespace collision between Contract '{0}' and 'Network.{0}'".format(name))
            self._network_dict[name] = ContractDeployer(name, interface)
        module.__dict__.update(self._network_dict)
        netconf = CONFIG['networks'][CONFIG['active_network']]
        if 'persist' in netconf and netconf['persist']:
            if not web3.eth.blockNumber:
                print(
                "WARNING: This appears to be a local RPC network. Persistence is not possible."
                "\n         Remove 'persist': true from config.json to silence this warning.")
                netconf['persist'] = False
        while True:
            if 'persist' not in netconf or not netconf['persist']:
                return
            exists = os.path.exists('environments/{}.env'.format(CONFIG['active_network']))
            if not exists:
                print("Persistent environment for '{}' has not yet been declared.".format(
                    CONFIG['active_network']))
                netconf['password'] = getpass(
                    "Please set a password for the persisten environment: ")
                return
            try:
                if 'password' not in netconf:
                    netconf['password'] = getpass(
                        "Enter the persistence password for '{}': ".format(
                            CONFIG['active_network']))
                encrypted = open("environments/"+CONFIG['active_network']+".env","r").read()
                decrypted = json.loads(FernetKey(netconf['password']).decrypt(encrypted))
                print("Loading persistent environment...")
                for priv_key in decrypted['accounts']:
                    self._network_dict['accounts'].add(priv_key)
                for contract,address in [(k,x) for k,v in decrypted['contracts'].items() for x in v]:
                    getattr(self,contract).at(*address)
                break
            except InvalidToken:
                print("Password is incorrect, please try again or CTRL-C to disable persistence.")
                del netconf['password']
            except KeyboardInterrupt:
                netconf['persist'] = False
                print("\nPersistence has been disabled.")


    def __del__(self):
        try:
            netconf = CONFIG['networks'][CONFIG['active_network']]
            if 'persist' not in netconf or not netconf['persist']:
                return
            print("Saving environment...")
            to_save = {'accounts':[], 'contracts':{}}
            for account in [i for i in self._network_dict['accounts'] if type(i) is LocalAccount]:
                to_save['accounts'].append(account._priv_key)
            for name, contract in [(k,v) for k,v in self._network_dict.items() if type(v) is ContractDeployer]:
                to_save['contracts'][name] = [[i.address, i.owner] for i in contract]
            encrypted = FernetKey(netconf['password']).encrypt(json.dumps(to_save), False)
            open("environments/"+CONFIG['active_network']+".env", 'w').write(encrypted)
        except Exception as e:
            if CONFIG['logging']['exc']>=2:
                print("".join(traceback.format_tb(sys.exc_info()[2])))
            print("ERROR: Unable to save environment due to unhandled {}: {}".format(
                type(e).__name__, e))

    def run(self, name):
        if not os.path.exists('deployments/{}.py'.format(name)):
            print("ERROR: Cannot find deployments/{}.py".format(name))
        module = importlib.import_module("deployments."+name)
        module.__dict__.update(self._network_dict)
        module.deploy()

    def reset(self, network=None):
        if network:
            if network not in CONFIG['networks']:
                print("ERROR: Network '{}' is not defined in config.json".format(network))
            CONFIG['active_network'] = network
        web3._reset()
        self.__init__(self._module)
        print("Brownie environment is ready.")

    def logging(self, **kwargs):
        if not kwargs or [k for k,v in kwargs.items() if
            k not in ('tx','exc') or type(v) is not int or not 0<=v<=2]:
            print("logging(tx=n, exc=n)\n\n 0 - Quiet\n 1 - Normal\n 2 - Verbose")
        else:
            CONFIG['logging'].update(kwargs)
            print(CONFIG['logging'])