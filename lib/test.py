#!/usr/bin/python3

import importlib
import os
import sys


if "--help" in sys.argv:
    sys.exit("""Usage: brownie test [filename] [options]

Options:
  [filename]         Only run tests from a specific file
  --network [name]   Use a specific network outlined in config.json (default development)
  --verbose          Show full traceback when a test fails

By default, brownie will load every .py file found in the tests folder and call every
function with a name starting in test.  A fresh environment is created before each test
by calling the setup function in the base_setup file (if present) as well as the setup
function in the active file.
""")

from lib.components.config import CONFIG
from lib.components.network import Network

sys.path.insert(0,"")

if len(sys.argv)>2 and sys.argv[2][:2]!="--":
    if not os.path.exists('tests/{}.py'.format(sys.argv[2])):
        sys.exit("ERROR: Cannot find tests/{}.py".format(sys.argv[2]))
    test_files = [sys.argv[2]]
else:
    test_files = [i[:-3] for i in os.listdir('tests') if i[-3:] == ".py" and i[:5] != "setup"]
    test_files.remove('__init__')



for name in test_files:
    module = importlib.import_module("tests."+name)
    test_names = open("tests/{}.py".format(name),'r').read().split("\ndef ")[1:]
    test_names = [i.split("(")[0] for i in test_names if i[0]!="_"]
    if not test_names:
        print("WARNING: Could not find any test functions in {}.py".format(name))
        continue
    if hasattr(module, "SETUP_MODULE"):
        setup = importlib.import_module("tests."+module.SETUP_MODULE.rstrip('.py'))
        setup.setup(network, network.accounts)
    print("Found {} tests in '{}'".format(len(test_names),name))
    for c,t in enumerate(test_names, start=1):
        network = Network()
        fn = getattr(module,t)
        if fn.__doc__:
            print("{} ({}/{})...".format(fn.__doc__,c,len(test_names)))
        else:
            print("Running test '{}' ({}/{})...".format(t,c,len(test_names)))
        try:
            getattr(module,t)(network, network.accounts)
        except Exception as e:
            print("ERROR: '{}' has failed due to {} - {}".format(t, type(e).__name__, e))