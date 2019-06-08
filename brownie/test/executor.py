#!/usr/bin/python3

from pathlib import Path
from requests.exceptions import ReadTimeout
import sys
import time

from . import pathutils
from .output import TestPrinter, cprint
from brownie.network import history, rpc
from brownie.cli.utils import color
from brownie._config import ARGV
from brownie.test import coverage
from brownie.exceptions import ExpectedFailing
import brownie.network as network
from brownie.network.contract import Contract


def run_test_modules(test_data, save):
    TestPrinter.set_grand_total(len(test_data))
    count = sum([len([x for x in i[3] if x[0] != "setup"]) for i in test_data])
    print("Running {} tests across {} modules.".format(count, len(test_data)))
    traceback_info = []
    start_time = time.time()
    try:
        for (module, build_path, coverage_eval, method_data) in test_data:
            tb, cov, contracts = run_test(module, method_data)
            if tb:
                traceback_info += tb
                # if build_path.exists():
                #    build_path.unlink()
                # continue

            if not save:
                continue

            contract_names = set(i._name for i in contracts)
            contract_names |= set(x for i in contracts for x in i._build['dependencies'])
            pathutils.save_build_json(
                module.__file__,
                build_path,
                cov or coverage_eval,
                contract_names
            )

        if not traceback_info:
            cprint("SUCCESS", "All tests passed.")
    except KeyboardInterrupt:
        print("\n\nTest execution has been terminated by KeyboardInterrupt.")
        sys.exit()
    finally:
        print("\nTotal runtime: {:.4f}s".format(time.time() - start_time))
        if traceback_info:
            cprint("WARNING", "{} test{} failed".format(
                len(traceback_info),
                "s" if traceback_info else ""
            ))
            for err in traceback_info:
                print("\nTraceback for {0[0]}:\n{0[1]}".format(err))


def run_test(module, method_data):
    rpc.reset()

    p = TestPrinter(
        module.__file__,
        0 if method_data[0][0].__name__ == "setup" else 1,
        len(method_data)
    )

    coverage_eval = {}
    if method_data[0][0].__name__ == "setup":
        tb, coverage_eval = run_test_method(*method_data[0], {}, p)
        if tb:
            return tb, {}, set()
        del method_data[0]
    rpc.snapshot()
    traceback_info = []
    contracts = _get_contract_names()

    for fn, args in method_data:
        history.clear()
        network.rpc.revert()
        tb, coverage_eval = run_test_method(fn, args, coverage_eval, p)
        contracts |= _get_contract_names()
        traceback_info += tb
        if tb and tb[0][2] == ReadTimeout:
            raise ReadTimeout(
                "Timeout while communicating with RPC. Possibly the local client has crashed."
            )
    p.finish()
    return traceback_info, coverage_eval, contracts


def run_test_method(fn, args, coverage_eval, p):
    desc = fn.__doc__ or fn.__name__
    if args['skip']:
        p.skip(desc)
        return [], coverage_eval
    p.start(desc)
    traceback_info = []
    try:
        if ARGV['coverage'] and 'always_transact' in args:
            ARGV['always_transact'] = args['always_transact']
        fn()
        if ARGV['coverage']:
            ARGV['always_transact'] = True
            # coverage_eval = coverage.analyze(history.copy(), coverage_eval)
        if args['pending']:
            raise ExpectedFailing("Test was expected to fail")
        p.stop()
        # return [], coverage_eval
    except Exception as e:
        p.stop(e, args['pending'])
        if not args['pending'] or type(e) == ExpectedFailing:
            path = Path(sys.modules[fn.__module__].__file__).relative_to(sys.path[0])
            path = "{0[module]}{1}.{0[callable]}{2}{0}".format(color, str(path)[:-3], fn.__name__)
            tb = color.format_tb(sys.exc_info(), sys.modules[fn.__module__].__file__)
            traceback_info = [(path, tb, type(e))]
    coverage_eval = coverage.analyze(history.copy(), coverage_eval)
    return traceback_info, coverage_eval
    # return [(path, tb, type(e))], {}


def _get_contract_names():
    return set(
        i.contract_address for i in history if type(i.contract_address) is Contract and
        not i.contract_address._build['sourcePath'].startswith('<string')
    )
