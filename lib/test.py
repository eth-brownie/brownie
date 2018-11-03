#!/usr/bin/python3

import importlib
import os
import solc
from subprocess import Popen, DEVNULL
import sys
from web3 import Web3, HTTPProvider

from lib.components.config import CONFIG
from lib.components.network import Network

sys.path.insert(0,"")

if len(sys.argv)>2 and sys.argv[2][:2]!="--":
    if not os.path.exists('tests/{}.py'.format(sys.argv[2])):
        sys.exit("ERROR: Cannot find tests/{}.py".format(sys.argv[2]))
    test_files = [sys.argv[2]]
else:
    test_files = [i[:-3] for i in os.listdir('tests') if i[-3:] == ".py"]
    test_files.remove('__init__')

if os.path.exists('tests/{}.py'.format(CONFIG['setup'])):
    setup_module = importlib.import_module("tests.{}".format(CONFIG['setup']))
    if not hasattr(setup_module, 'setup'):
        sys.exit("ERROR: Setup module has no setup() function defined.")
    print("Imported setup module from tests/{}.py".format(CONFIG['setup']))
    test_files.remove(CONFIG['setup'])
else:
    setup_module = False
    print("WARNING: No setup module found.")

for name in test_files:
    module = importlib.import_module("tests."+name)
    test_names = [i for i in dir(module) if i[:4]=="test" and callable(getattr(module,i))]
    if not test_names:
        print("WARNING: Module '{}' has no test functions defined.")
        continue
    for c,t in enumerate(test_names, start=1):
        network = Network()
        if setup_module and not hasattr(module, 'NO_SETUP'):
            setup_module.setup(network, network.accounts)
        if hasattr(module, 'setup'):
            try: module.setup(network. network.accounts)
            except Exception as e:
                print("ERROR: {} while running setup function in {}.".format(e, name))
                break
        print("Running function '{}' in {} ({}/{})...".format(t,name,len(test_names),c))
        getattr(module,t)(network, network.accounts)