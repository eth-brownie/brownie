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



def _run_test(module, fn_name, count, total):
    fn = getattr(module, fn_name)
    desc = fn.__doc__ or fn_name
    sys.stdout.write("   {} ({}/{})...  ".format(desc, count, total))
    sys.stdout.flush()
    try:
        stime = time.time()
        fn()
        sys.stdout.write("\r {0[success]}\u2713{0} {1} ({2:.4f}s)\n".format(
            color, desc, time.time()-stime
        ))
        sys.stdout.flush()
        return []
    except Exception as e:
        sys.stdout.write("\r {0[error]}{1}{0[dull]} {2} ({0[error]}{3}{0[dull]}){0}\n".format(
            color, 
            '\u2717' if type(e) in (
                AssertionError,
                tx.VirtualMachineError
            ) else '\u203C',
            desc,
            type(e).__name__
        ))
        sys.stdout.flush()
        filename = module.__file__.lstrip('./')
        fn_name = filename[:-2]+fn_name
        return [(fn_name, color.format_tb(sys.exc_info(), filename))]


def run_test(filename, network):
    network.reset()
    if type(CONFIG['test']['gas_limit']) is int:
        network.gas(CONFIG['test']['gas_limit'])
    module = importlib.import_module("tests."+filename)
    test_names = open(
        "tests/{}.py".format(filename), 'r'
    ).read().split("\ndef ")[1:]
    test_names = [i.split("(")[0] for i in test_names if i[0]!="_"]
    traceback_info = []
    if not test_names:
        print("\n{0[error]}WARNING{0}: Cannot find test functions in {0[module]}{1}.py{0}".format(color, name))
        return [], []
    print("\nRunning {0[module]}{1}.py{0} - {2} test{3}".format(
            color, filename, len(test_names)-1,"s" if len(test_names)!=2 else ""
    ))
    if 'setup' in test_names:
        test_names.remove('setup')
        traceback_info += _run_test(module, 'setup', 0, len(test_names))
        if traceback_info:
            return tx.tx_history.copy(), traceback_info
    network.rpc.snapshot()
    for c,t in enumerate(test_names, start=1):
        network.rpc.revert()
        traceback_info += _run_test(module,t,c,len(test_names))
    return tx.tx_history.copy(), traceback_info

def main():
    args = docopt(__doc__)
    traceback_info = []
    if args['<filename>']:
        name = args['<filename>'].replace(".py", "")
        if not os.path.exists("tests/{}.py".format(name)):
            sys.exit("{0[error]}ERROR{0}: Cannot find {0[module]}tests/{1}.py{0}".format(color, name))
        test_files = [name]
    else:
        test_files = [i[:-3] for i in os.listdir("tests") if i[-3:] == ".py"]
        test_files.remove('__init__')

    network = Network()
    for filename in test_files:
        history, tb = run_test(filename, network)
        if tb:
            traceback_info += tb
    if not traceback_info:
        print("\n{0[success]}SUCCESS{0}: All tests passed.".format(color))
        if '--gas' in sys.argv:
            print('\nGas Profile:')
            for i in sorted(tx.gas_profile):
                print("{0} -  avg: {1[avg]:.0f}  low: {1[low]}  high: {1[high]}".format(i, tx.gas_profile[i]))
        sys.exit()

    print("\n{0[error]}WARNING{0}: {1} test{2} failed.{0}".format(
        color, len(traceback_info), "s" if len(traceback_info)>1 else ""
    ))

    for err in traceback_info:
        print("\nException info for {0[0]}:\n{0[1]}".format(err))