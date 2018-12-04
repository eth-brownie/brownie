#!/usr/bin/python3

import importlib
import os
import sys
import time
import traceback

from lib.components.eth import VirtualMachineError

if "--help" in sys.argv:
    sys.exit("""Usage: brownie test [filename] [options]

Options:
  [filename]         Only run tests from a specific file

By default brownie runs every script in the tests folder, and calls every
function that does not begin with an underscore. A fresh environment is created
between each new file. Test scripts can optionally specify which deployment
script to run by setting a string 'DEPLOYMENT'.""")

if len(sys.argv)>2 and sys.argv[2][:2]!="--":
    sys.argv[2] = sys.argv[2].replace('.py','')
    if not os.path.exists('tests/{}.py'.format(sys.argv[2])):
        sys.exit("ERROR: Cannot find tests/{}.py".format(sys.argv[2]))
    test_files = [sys.argv[2]]
else:
    test_files = [i[:-3] for i in os.listdir('tests') if i[-3:] == ".py"]
    test_files.remove('__init__')

from lib.components.config import CONFIG
from lib.components.network import Network

traceback_info = []

def _format_tb(test, desc, exc, match):
    sys.stdout.write("\r \033[91m{}\x1b[0m {} ({})\n".format(
        '\u2717' if exc[0] in (AssertionError, VirtualMachineError) else '\u203C',
        desc, exc[0].__name__ ))
    sys.stdout.flush()
    traceback_info.append((test, "{}  {}: {}".format(
        next(i for i in traceback.format_tb(exc[2])[::-1] if match in i),
        exc[0].__name__, exc[1])))

for name in test_files:
    module = importlib.import_module("tests."+name)
    test_names = open("tests/{}.py".format(name),'r').read().split("\ndef ")[1:]
    test_names = [i.split("(")[0] for i in test_names if i[0]!="_"]
    if not test_names:
        print("\nWARNING: Could not find any test functions in {}.py".format(name))
        continue
    print("\nRunning {}.py - {} test{}".format(
            name, len(test_names),"s" if len(test_names)!=1 else ""))
    Network(module)
    if hasattr(module, 'DEPLOYMENT'):
        sys.stdout.write("   Deployment '{}'...".format(module.DEPLOYMENT))
        sys.stdout.flush()
        try:
            stime = time.time()
            module.run(module.DEPLOYMENT)
            sys.stdout.write("\r \033[92m\u2713\x1b[0m Deployment '{}' ({:.4f}s)\n".format(
                module.DEPLOYMENT,time.time()-stime))
            sys.stdout.flush()
        except Exception as e:
            _format_tb(
                "{}.deploy".format(module.DEPLOYMENT),
                "Deployment '{}'".format(module.DEPLOYMENT),
                sys.exc_info(),
                'deployments/'+module.DEPLOYMENT)
            continue
    for c,t in enumerate(test_names, start=1):
        fn = getattr(module,t)
        sys.stdout.write("   {} ({}/{})...  ".format(
            fn.__doc__ or t,c,len(test_names)))
        sys.stdout.flush()
        try:
            stime = time.time()
            fn()
            sys.stdout.write("\r \033[92m\u2713\x1b[0m {} ({:.4f}s)\n".format(
                fn.__doc__ or t,time.time()-stime))
            sys.stdout.flush()
        except Exception as e:
            _format_tb(
                "{}.{}".format(name,t),
                fn.__doc__ or t,
                sys.exc_info(),
                'tests/'+name)

if not traceback_info:
    sys.exit("\nSUCCESS: All tests passed.")

print("\nWARNING: {} test{} failed.".format(
    len(traceback_info), "s" if len(traceback_info)>1 else ""))

for err in traceback_info:
    print("\nException info for {0[0]}:\n{0[1]}".format(err))