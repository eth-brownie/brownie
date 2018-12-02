#!/usr/bin/python3

import importlib
import os
import sys
import time
import traceback

from lib.components.account import VirtualMachineError

if "--help" in sys.argv:
    sys.exit("""Usage: brownie test [filename] [options]

Options:
  [filename]         Only run tests from a specific file

By default brownie runs every script in the tests folder, and calls every
function that does not begin with an underscore. A fresh environment is created
between each new file. Test scripts can optionally specify which deployment
script to run by setting a string 'DEPLOYMENT'.""")

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
    Network(module)
    print("{}: {} test{}".format(
            name, len(test_names),"s" if len(test_names)!=1 else ""))
    for c,t in enumerate(test_names, start=1):
        fn = getattr(module,t)
        if fn.__doc__:
            sys.stdout.write("  {} ({}/{})...  ".format(fn.__doc__,c,len(test_names)))
        else:
            sys.stdout.write("  Running test '{}' ({}/{})...  ".format(t,c,len(test_names)))
        sys.stdout.flush()
        try:
            sblock, stime = module.eth.blockNumber, time.time()
            fn()
            print("\033[92m\u2713\x1b[0m ({} tx in {:.4f}s)".format(
                module.eth.blockNumber-sblock,time.time()-stime))
        except AssertionError as e:
            if CONFIG['logging']['exc']>=2:
                print("\033[91m\u2717\x1b[0m\n\n{}{}: {}\n".format(
                    traceback.format_tb(sys.exc_info()[2])[-2],
                    sys.exc_info()[0].__name__,
                    sys.exc_info()[1]
                    ))
            else:
                print("\033[91m\u2717\x1b[0m ({})".format(e))
        except VirtualMachineError as e:
            if CONFIG['logging']['exc']>=2:
                print("\033[91m\u2717\x1b[0m\n\n{}{}: {}\n".format(
                    traceback.format_tb(sys.exc_info()[2])[-3],
                    sys.exc_info()[0].__name__,
                    sys.exc_info()[1]
                    ))
            else:
                print("\033[91m\u2717\x1b[0m ({})".format(e))
        except Exception as e:
            if CONFIG['logging']['exc']>=2:
                print("\033[91m\u203C\x1b[0m\n\n{}{}: {}\n".format(
                    ''.join(traceback.format_tb(sys.exc_info()[2])),
                    sys.exc_info()[0].__name__,
                    sys.exc_info()[1]
                    ))
            else:
                print("\033[91m\u203C\x1b[0m ({})".format(type(e).__name__))