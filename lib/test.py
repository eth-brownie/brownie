#!/usr/bin/python3

from docopt import docopt
import importlib
import os
import sys
import time

from lib.components.network import Network
from lib.components import transaction as tx
from lib.services import color
from lib.services import config
CONFIG = config.CONFIG


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


def _format_tb(test, desc, exc, filename):
    sys.stdout.write("\r {0[red]}{1}{0[dark white]} {2} ({0[red]}{3}{0[dark white]}){0}\n".format(
        color, 
        '\u2717' if exc[0] in (
            AssertionError,
            tx.VirtualMachineError
        ) else '\u203C',
        desc,
        exc[0].__name__
    ))
    sys.stdout.flush()
    return (test, color.format_tb(exc, filename))


def run_test(filename):
    module = importlib.import_module("tests."+filename)
    test_names = open(
        "tests/{}.py".format(filename), 'r'
    ).read().split("\ndef ")[1:]
    test_names = [i.split("(")[0] for i in test_names if i[0]!="_"]
    if not test_names:
        print("\n{0[bright red]}WARNING{0}: Cannot find test functions in {0[bright yellow]}{1}.py{0}".format(color, name))
        return [], False
    network = Network(module)
    print("\nRunning {0[bright yellow]}{1}.py{0} - {2} test{3}".format(
            color, filename, len(test_names),"s" if len(test_names)!=1 else ""
    ))
    if hasattr(module, 'DEPLOYMENT'):
        sys.stdout.write("   Deployment '{}'...".format(module.DEPLOYMENT))
        sys.stdout.flush()
        try:
            stime = time.time()
            module.run(module.DEPLOYMENT)
            sys.stdout.write(
                "\r {0[bright green]}\u2713{0} Deployment '{1}' ({2:.4f}s)\n".format(
                    color, module.DEPLOYMENT, time.time()-stime
                )
            )
            sys.stdout.flush()
        except Exception as e:
            return tx.tx_history.copy(), _format_tb(
                "{}.deploy".format(module.DEPLOYMENT),
                "Deployment '{}'".format(module.DEPLOYMENT),
                sys.exc_info(),
                "deployments/"+module.DEPLOYMENT
            )
    for c,t in enumerate(test_names, start=1):
        fn = getattr(module,t)
        sys.stdout.write("   {} ({}/{})...  ".format(
            fn.__doc__ or t,c,len(test_names)
        ))
        sys.stdout.flush()
        try:
            stime = time.time()
            fn()
            sys.stdout.write("\r {0[bright green]}\u2713{0} {1} ({2:.4f}s)\n".format(
                color, fn.__doc__ or t, time.time()-stime
            ))
            sys.stdout.flush()
        except Exception as e:
            return tx.tx_history.copy(), _format_tb(
                "{}.{}".format(filename,t),
                fn.__doc__ or t,
                sys.exc_info(),
                "tests/"+filename
            )
    return tx.tx_history.copy(), False

def main():
    args = docopt(__doc__)
    traceback_info = []
    if args['<filename>']:
        name = args['<filename>'].replace(".py", "")
        if not os.path.exists("tests/{}.py".format(name)):
            sys.exit("{0[bright red]}ERROR{0}: Cannot find {0[bright yellow]}tests/{1}.py{0}".format(color, name))
        test_files = [name]
    else:
        test_files = [i[:-3] for i in os.listdir("tests") if i[-3:] == ".py"]
        test_files.remove('__init__')

    for filename in test_files:
        history, tb = run_test(filename)
        if tb:
            traceback_info.append(tb)

    if not traceback_info:
        print("\n{0[bright green]}SUCCESS{0}: All tests passed.".format(color))
        if '--gas' in sys.argv:
            print('\nGas Profile:')
            for i in sorted(tx.gas_profile):
                print("{0} -  avg: {1[avg]:.0f}  low: {1[low]}  high: {1[high]}".format(i, tx.gas_profile[i]))
        sys.exit()

    print("\n{0[bright red]}WARNING{0}: {1} test{2} failed.{0}".format(
        color, len(traceback_info), "s" if len(traceback_info)>1 else ""
    ))

    for err in traceback_info:
        print("\nException info for {0[0]}:\n{0[1]}".format(err))