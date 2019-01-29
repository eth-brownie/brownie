#!/usr/bin/python3

from getpass import getpass
import importlib
import json
import os
import sys
import traceback

from lib.components import alert
from lib.components.eth import Rpc, web3, wei
from lib.components import contract
from lib.components.account import Accounts, LocalAccount
from lib.components import transaction as tx
import lib.components.check as check
from lib.services.fernet import FernetKey, InvalidToken
from lib.services import compiler
from lib.services import config
CONFIG = config.CONFIG


class Network:

    _key = None
    _init = True
    _rpc = None

    def __init__(self, module):
        self._key = None
        self._init = True
        self._network_dict = {'rpc': None}
        self._module = module
        self.setup()

    
    def setup(self):
        if self._init or sys.argv[1] == "console":
            verbose = True
            self._init = False
        else:
            verbose = False
        if self._network_dict['rpc']:
            self._network_dict['rpc']._kill()
        if verbose:
            print("Using network '{}'".format(CONFIG['active_network']['name']))
        if 'test-rpc' in CONFIG['active_network']:
            if verbose:
                print("Running '{}'...".format(CONFIG['active_network']['test-rpc']))
            rpc = Rpc(self)
        else:
            rpc = None
        web3._connect()
        accounts = Accounts(web3.eth.accounts)
        tx.tx_history.clear()
        self._network_dict = {
            'a': accounts,
            'accounts': accounts,
            'alert': alert,
            'check': check,
            'gas': gas,
            'history': tx.tx_history,
            'logging': logging,
            'reset': self.reset,
            'run': self.run,
            'rpc': rpc,
            'web3': web3,
            'wei': wei
        }
        for name, build in compiler.compile_contracts().items():
            if build['type'] == "interface":
                continue
            if name in self._network_dict:
                raise AttributeError("Namespace collision between Contract '{0}' and 'Network.{0}'".format(name))
            self._network_dict[name] = contract.ContractDeployer(build, self._network_dict)
        self._module.__dict__.update(self._network_dict)
        if not CONFIG['active_network']['persist']:
            return
        while True:
            persist_file = "build/networks/{}.json".format(CONFIG['active_network']['name'])
            exists = os.path.exists(persist_file)
            if not exists:
                print("Persistent environment for '{}' has not yet been declared.".format(
                    CONFIG['active_network']['name']))
                self._key = FernetKey(getpass(
                    "Please set a password for the persistent environment: "
                ))
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
                        "\n         Remove 'persist': true from config.json to silence this warning."
                    )
                    CONFIG['active_network']['persist'] = False
                    return
                if not self._key:
                    self._key = FernetKey(getpass(
                        "Enter the persistence password for '{}': ".format(
                            CONFIG['active_network']['name'])))
                self._key.decrypt(data['password'])
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
            if not CONFIG['active_network']['persist']:
                return
            print("Saving environment...")
            to_save = []
            for account in [i for i in self._network_dict['accounts'] if type(i) is LocalAccount]:
                to_save.append(self._key.encrypt(account._priv_key, False))
            persist_file = CONFIG['folders']['project']+'/build/networks/{}.json'.format(CONFIG['active_network'])
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
        if not os.path.exists("deployments/{}.py".format(name)):
            print("ERROR: Cannot find deployments/{}.py".format(name))
            return
        module = importlib.import_module("deployments."+name)
        module.__dict__.update(self._network_dict)
        module.deploy()

    def reset(self, network=None):
        alert.stop_all()
        if network and CONFIG[network] != CONFIG['active_network']:
            self.save()
            config.set_network(network)
            self._key = None
        contract.deployed_contracts.clear()
        if CONFIG['active_network']['persist']:
            compiler.clear_persistence(CONFIG['active_network']['name'])
        self.setup()
        return "Brownie environment is ready."

def logging(**kwargs):
    if not kwargs or [k for k,v in kwargs.items() if
        k not in ('tx','exc') or type(v) is not int or not 0<=v<=2]:
        print("logging(tx=n, exc=n)\n\n 0 - Quiet\n 1 - Normal\n 2 - Verbose")
    else:
        CONFIG['logging'].update(kwargs)
        print(CONFIG['logging'])

def gas(*args):
    if args:
        if args[0] in ("auto", None, False, True):
            CONFIG['active_network']['gas_limit'] = False
        else:
            try:
                CONFIG['active_network']['gas_limit'] = int(args[0])
            except:
                return "Invalid gas limit."
    return "Gas limit is set to {}".format(
        CONFIG['active_network']['gas_limit'] or "automatic"
    )

    