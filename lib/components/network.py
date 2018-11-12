#!/usr/bin/python3

from getpass import getpass
import importlib
import json
import os
import sys
import traceback

from lib.services.fernet import FernetKey
from lib.components.config import CONFIG
from lib.components.eth import web3, COMPILED
from lib.components.account import Accounts, LocalAccount
from lib.components.contract import ContractDeployer
import lib.components.check as check


class Network:

    check = check

    def __init__(self, module):
        self._clean_dict = list(module.__dict__)
        self._module = module
        self.accounts = Accounts(web3.eth.accounts)
        for name, interface in COMPILED.items():
            setattr(self, name.split(':')[-1], ContractDeployer(interface))
        self._network_dict = dict(
            [(i,getattr(self,i)) for i in dir(self) if i[0]!='_'] +
            [(i,getattr(web3,i)) for i in dir(web3) if i[0].islower()])
        module.__dict__.update(self._network_dict)
        netconf = CONFIG['networks'][CONFIG['default_network']]
        if 'persist' in netconf and netconf['persist']:
            if not web3.eth.blockNumber:
                print(
                "WARNING: This appears to be a local RPC network. Persistence is not possible."
                "\n         Remove 'persist': true from config.json to silence this warning.")
            netconf['persist'] = False
        if 'persist' in netconf and netconf['persist']:
            if 'password' not in netconf:
                netconf['password'] = getpass(
                    "Enter the persistence password for '{}': ".format(
                        CONFIG['default_network']))
            if os.path.exists(CONFIG['default_network']+".brownie"):
                print("Loading persistent environment...")
                encrypted = open("environments/"+CONFIG['default_network']+".brownie","r").read()
                decrypted = json.loads(FernetKey(netconf['password']).decrypt(encrypted))
                for priv_key in decrypted['accounts']:
                    self.accounts.add(priv_key)
                for contract,address in [(k,x) for k,v in decrypted['contracts'].items() for x in v]:
                    getattr(self,contract).at(*address) 
        print("Brownie environment is ready.")
        if hasattr(module, 'DEPLOYMENT'):
            self.run(module.DEPLOYMENT)

    def __del__(self):
        try:
            netconf = CONFIG['networks'][CONFIG['default_network']]
            if 'persist' not in netconf or not netconf['persist']:
                return
            print("Saving environment...")
            to_save = {'accounts':[], 'contracts':{}}
            for account in [i for i in self.accounts if type(i) is LocalAccount]:
                to_save['accounts'].append(account._priv_key)
            for name, contract in [(k,v) for k,v in self.__dict__.items() if type(v) is ContractDeployer]:
                to_save['contracts'][name] = [[i.address, i.owner] for i in contract]
            encrypted = FernetKey(netconf['password']).encrypt(json.dumps(to_save), False)
            open("environments/"+CONFIG['default_network']+".brownie", 'w').write(encrypted)
        except Exception as e:
            if CONFIG['logging']['exc']>=2:
                print("".join(traceback.format_tb(sys.exc_info()[2])))
            print("ERROR: Unable to save environment due to unhandled {}: {}".format(
                type(e).__name__, e))

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

    def logging(self, **kwargs):
        if not kwargs or [k for k,v in kwargs.items() if
            k not in ('tx','exc') or type(v) is not int or not 0<=v<=2]:
            print("logging(tx=n, exc=n)\n\n 0 - Quiet\n 1 - Normal\n 2 - Verbose")
        else:
            CONFIG['logging'].update(kwargs)
            print(CONFIG['logging'])