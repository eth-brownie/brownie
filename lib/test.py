#!/usr/bin/python3

from docopt import docopt
import importlib
import os
import sys
import time
import traceback

from lib.components.eth import VirtualMachineError,TransactionReceipt
from lib.components.network import Network
from lib.components import config
CONFIG = config.CONFIG


GREEN = "\033[92m"
RED = "\033[91m"
DEFAULT = "\x1b[0m"

__doc__ = """Usage: brownie test [<filename>] [options]

Arguments:
  <filename>         Only run tests from a specific file

Options:
  --help             Display this message
  --verbose          Enable verbose reporting
  --gas              Display gas profile for function calls

By default brownie runs every script in the tests folder, and calls every
function that does not begin with an underscore. A fresh environment is created
between each new file. Test scripts can optionally specify which deployment
script to run by setting a string 'DEPLOYMENT'."""


traceback_info = []

def _format_tb(test, desc, exc, match):
    sys.stdout.write("{}{}{} {} ({})\n".format(
        RED, 
        '\u2717' if exc[0] in (
            AssertionError,
            VirtualMachineError
        ) else '\u203C',
        DEFAULT,
        desc, exc[0].__name__
    ))
    sys.stdout.flush()
    abs_path = os.path.abspath(".")+"/"
    tb = [i.replace(abs_path, "") for i in traceback.format_tb(exc[2])]
    start = tb.index(next(i for i in tb if match in i))
    stop = tb.index(next(i for i in tb[::-1] if match in i)) + 1
    traceback_info.append((test, "{}  {}: {}".format(
        "".join(tb[start:stop]), exc[0].__name__, exc[1]
    )))


def main():
    args = docopt(__doc__)
    if args['<filename>']:
        name = args['<filename>'].replace(".py", "")
        if not os.path.exists("tests/{}.py".format(name)):
            sys.exit("ERROR: Cannot find tests/{}.py".format(name))
        test_files = [name]
    else:
        test_files = [i[:-3] for i in os.listdir("tests") if i[-3:] == ".py"]
        test_files.remove('__init__')

    network = None
    for name in test_files:
        module = importlib.import_module("tests."+name)
        test_names = open(
            "tests/{}.py".format(name), 'r'
        ).read().split("\ndef ")[1:]
        test_names = [i.split("(")[0] for i in test_names if i[0]!="_"]
        if not test_names:
            print("\nWARNING: Cannot find test functions in {}.py".format(name))
            continue
        
        if network:
            network.reset()
        print("\nRunning {}.py - {} test{}".format(
                name, len(test_names),"s" if len(test_names)!=1 else ""
        ))
        network = Network(module)
        if hasattr(module, 'DEPLOYMENT'):
            sys.stdout.write("   Deployment '{}'...".format(module.DEPLOYMENT))
            sys.stdout.flush()
            try:
                stime = time.time()
                module.run(module.DEPLOYMENT)
                sys.stdout.write(
                    "\r {}\u2713{} Deployment '{}' ({:.4f}s)\n".format(
                        GREEN, DEFAULT, module.DEPLOYMENT, time.time()-stime
                    )
                )
                sys.stdout.flush()
            except Exception as e:
                _format_tb(
                    "{}.deploy".format(module.DEPLOYMENT),
                    "Deployment '{}'".format(module.DEPLOYMENT),
                    sys.exc_info(),
                    "deployments/"+module.DEPLOYMENT
                )
                continue
        for c,t in enumerate(test_names, start=1):
            fn = getattr(module,t)
            sys.stdout.write("   {} ({}/{})...  ".format(
                fn.__doc__ or t,c,len(test_names)
            ))
            sys.stdout.flush()
            try:
                stime = time.time()
                fn()
                sys.stdout.write("\r {}\u2713{} {} ({:.4f}s)\n".format(
                    GREEN, DEFAULT, fn.__doc__ or t, time.time()-stime
                ))
                sys.stdout.flush()
            except Exception as e:
                _format_tb(
                    "{}.{}".format(name,t),
                    fn.__doc__ or t,
                    sys.exc_info(),
                    "tests/"+name
                )

    if not traceback_info:
        print("\n{}SUCCESS: All tests passed.{}".format(GREEN, DEFAULT))
        if '--gas' in sys.argv:
            print('\nGas Profile:')
            for i in sorted(TransactionReceipt._gas_profiles):
                print("{0} -  avg: {1[avg]:.0f}  low: {1[low]}  high: {1[high]}".format(i,TransactionReceipt._gas_profiles[i]))
        sys.exit()

    print("\n{}WARNING: {} test{} failed.{}".format(
        RED, len(traceback_info), "s" if len(traceback_info)>1 else "", DEFAULT
    ))

    for err in traceback_info:
        print("\nException info for {0[0]}:\n{0[1]}".format(err))