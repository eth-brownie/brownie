#!/usr/bin/python3

import importlib
import os
import sys
import traceback


PASS = "\033[92m\u2713\x1b[0m"
FAIL = "\033[91m\u2717\x1b[0m"



if "--help" in sys.argv:
    sys.exit("""Usage: brownie test [filename] [options]

Options:
  [filename]         Only run tests from a specific file
  --network [name]   Use a specific network outlined in config.json (default development)
  --verbose          Show full traceback when a test fails

By default brownie runs every python script in the tests folder, and calls every
function that does not begin with an underscore. A fresh environment is created
between each new file. Test scripts can optionally specify which deployment
script to run by setting a string 'DEPLOYMENT'.""")

sys.path.insert(0, "")

if len(sys.argv)>2 and sys.argv[2][:2]!="--":
    if not os.path.exists('tests/{}.py'.format(sys.argv[2])):
        sys.exit("ERROR: Cannot find tests/{}.py".format(sys.argv[2]))
    test_files = [sys.argv[2]]
else:
    test_files = [i[:-3] for i in os.listdir('tests') if i[-3:] == ".py"]
    test_files.remove('__init__')

from lib.components.config import CONFIG
from lib.components.network import Network

for name in test_files:
    module = importlib.import_module("tests."+name)
    test_names = open("tests/{}.py".format(name),'r').read().split("\ndef ")[1:]
    test_names = [i.split("(")[0] for i in test_names if i[0]!="_"]
    if not test_names:
        print("WARNING: Could not find any test functions in {}.py".format(name))
        continue
    if hasattr(module, "DEPLOYMENT"):
        setup = importlib.import_module("deployments."+module.SETUP_MODULE.rstrip('.py'))
        setup.setup(network, network.accounts)
    print("Found {} tests in '{}'".format(len(test_names),name))
    for c,t in enumerate(test_names, start=1):
        network = Network()
        fn = getattr(module,t)
        if fn.__doc__:
            sys.stdout.write("{} ({}/{})...  ".format(fn.__doc__,c,len(test_names)))
        else:
            sys.stdout.write("Running test '{}' ({}/{})...  ".format(t,c,len(test_names)))
        try:
            fn(network, network.accounts)
            print('okaaay')
            print(PASS)
        except AssertionError as e:
            print(FAIL+" ({})".format(e))
        except Exception as e:
            if '--verbose' in sys.argv:
                print(FAIL+"\n\n{}{}: {}\n".format(
                    ''.join(traceback.format_tb(sys.exc_info()[2])),
                    sys.exc_info()[0].__name__,
                    sys.exc_info()[1]
                    ))
            else:
                print(FAIL+" (unhandled {})".format(type(e).__name__))