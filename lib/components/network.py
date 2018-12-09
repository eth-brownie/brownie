#!/usr/bin/python3

from getpass import getpass
import importlib
import json
import os
import sys
import traceback

from lib.services.fernet import FernetKey, InvalidToken
from lib.components.config import CONFIG
from lib.components.eth import web3, wei, compile_contracts, get_compiled, clear_contracts
import lib.components.eth as ethh
from lib.components.account import Accounts, LocalAccount
from lib.components.contract import ContractDeployer
import lib.components.check as check


class Network:

    _key = None

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
        for name, interface in get_compiled().items():
            if name in self._network_dict:
                raise AttributeError("Namespace collision between Contract '{0}' and 'Network.{0}'".format(name))
            self._network_dict[name] = ContractDeployer(name, interface, CONFIG['active_network'])
        module.__dict__.update(self._network_dict)
        netconf = CONFIG['networks'][CONFIG['active_network']]
        if 'persist' not in netconf or not netconf['persist']:
            return
        while True:
            persist_file = 'build/networks/{}.json'.format(CONFIG['active_network'])
            exists = os.path.exists(persist_file)
            if not exists:
                print("Persistent environment for '{}' has not yet been declared.".format(
                    CONFIG['active_network']))
                self._key = FernetKey(getpass(
                    "Please set a password for the persistent environment: "))
                json.dump({
                    'height': web3.eth.blockNumber,
                    'password': self._key.encrypt('password', False)},
                    open(persist_file, 'w'), sort_keys=True, indent=4)
                return
            try:
                data = json.load(open(persist_file))
                if data['height'] > web3.eth.blockNumber:
                    print(
                        "WARNING: This appears to be a local RPC network. Persistence is not possible."
                        "\n         Remove 'persist': true from config.json to silence this warning.")
                    netconf['persist'] = False
                    return
                if not self._key:
                    self._key = FernetKey(getpass(
                        "Enter the persistence password for '{}': ".format(
                            CONFIG['active_network'])))
                self._key.decrypt(data['password'])
                print(self._key)
                print("Loading persistent environment...")
                for priv_key in data['accounts']:
                    self._network_dict['accounts'].add(self._key.decrypt(priv_key))
                break
            except InvalidToken:
                self._key = None
                print("Password is incorrect, please try again or CTRL-C to disable persistence.")
            except KeyboardInterrupt:
                self._key = None
                print("\nPersistence has been disabled.")
                return


    def save(self):
        try:
            netconf = CONFIG['networks'][CONFIG['active_network']]
            if 'persist' not in netconf or not netconf['persist']:
                return
            print("Saving environment...")
            to_save = []
            for account in [i for i in self._network_dict['accounts'] if type(i) is LocalAccount]:
                to_save.append(self._key.encrypt(account._priv_key, False))
            persist_file = 'build/networks/{}.json'.format(CONFIG['active_network'])
            data = json.load(open(persist_file))
            data['height'] = web3.eth.blockNumber
            data['accounts'] = to_save
            json.dump(data, open(persist_file,'w'), sort_keys=True, indent=4)
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
            if network != CONFIG['active_network']:
                self.save()
                CONFIG['active_network'] = network
                self._key = None
        web3._reset()
        netconf = CONFIG['networks'][CONFIG['active_network']]
        if 'persist' in netconf and netconf['persist']:
            clear_contracts(CONFIG['active_network'])
        compile_contracts()
        self.__init__(self._module)
        print("Brownie environment is ready.")

    def logging(self, **kwargs):
        if not kwargs or [k for k,v in kwargs.items() if
            k not in ('tx','exc') or type(v) is not int or not 0<=v<=2]:
            print("logging(tx=n, exc=n)\n\n 0 - Quiet\n 1 - Normal\n 2 - Verbose")
        else:
            CONFIG['logging'].update(kwargs)
            print(CONFIG['logging'])