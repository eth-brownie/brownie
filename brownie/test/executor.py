#!/usr/bin/python3

from pathlib import Path
from requests.exceptions import ReadTimeout
import sys
import time

from . import pathutils, loader
from .output import TestPrinter, cprint
from brownie.network import history, rpc
from brownie.cli.utils import color
from brownie._config import ARGV
from brownie.test import coverage
from brownie.exceptions import ExpectedFailing
import brownie.network as network
from brownie.network.contract import Contract


def _get_test_data(test_paths, only_update, check_coverage):
    test_data = []
    for path in test_paths:
        build_json = pathutils.get_build_json(path)
        if build_json['sha1'] and only_update:
            continue
        fn_list = loader.get_methods(path, check_coverage)
        if not fn_list:
            continue
        # test path, build data, list of (fn, args)
        test_data.append((path, build_json, fn_list))
    return test_data


def run_test_modules(test_paths, only_update=True, check_coverage=False, save=True):
    test_data = _get_test_data(test_paths, only_update, check_coverage)
    if not test_data:
        if test_paths and only_update:
            cprint("SUCCESS", "All test results are up to date.")
        else:
            cprint("WARNING", "No tests were found.")
        return
    TestPrinter.set_grand_total(len(test_data))
    print("Running {} tests across {} module{}.".format(
        sum([len([x for x in i[2] if x[0].__name__ != "setup"]) for i in test_data]),
        len(test_data),
        "s" if len(test_data) > 1 else ""
    ))
    traceback_info = []
    start_time = time.time()
    try:
        for (test_path, old_coverage_eval, method_data) in test_data:
            tb, coverage_eval, contracts = run_test(test_path, method_data)
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
                test_path,
                coverage_eval or old_coverage_eval,
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
                "s" if len(traceback_info) > 1 else ""
            ))
            for err in traceback_info:
                print("\nTraceback for {0[0]}:\n{0[1]}".format(err))


def run_test(test_path, method_data):
    rpc.reset()

    printer = TestPrinter(
        test_path,
        0 if method_data[0][0].__name__ == "setup" else 1,
        len(method_data)
    )

    coverage_eval = {}
    if method_data[0][0].__name__ == "setup":
        tb, coverage_eval = run_test_method(*method_data[0], {}, printer)
        if tb:
            return tb, {}, set()
        del method_data[0]
    rpc.snapshot()
    traceback_info = []
    contracts = _get_contract_names()

    for fn, args in method_data:
        history.clear()
        network.rpc.revert()
        tb, coverage_eval = run_test_method(fn, args, coverage_eval, printer)
        contracts |= _get_contract_names()
        traceback_info += tb
        if tb and tb[0][2] == ReadTimeout:
            raise ReadTimeout(
                "Timeout while communicating with RPC. Possibly the local client has crashed."
            )
    printer.finish()
    return traceback_info, coverage_eval, contracts


def run_test_method(fn, args, coverage_eval, printer):
    desc = fn.__doc__ or fn.__name__
    if args['skip']:
        printer.skip(desc)
        return [], coverage_eval
    printer.start(desc)
    traceback_info = []
    try:
        if ARGV['coverage'] and 'always_transact' in args:
            ARGV['always_transact'] = args['always_transact']
        fn()
        if ARGV['coverage']:
            ARGV['always_transact'] = True
        if args['pending']:
            raise ExpectedFailing("Test was expected to fail")
        printer.stop()
    except Exception as e:
        printer.stop(e, args['pending'])
        if not args['pending'] or type(e) == ExpectedFailing:
            path = Path(sys.modules[fn.__module__].__file__).relative_to(sys.path[0])
            path = "{0[module]}{1}.{0[callable]}{2}{0}".format(color, str(path)[:-3], fn.__name__)
            tb = color.format_tb(sys.exc_info(), sys.modules[fn.__module__].__file__)
            traceback_info = [(path, tb, type(e))]
    coverage_eval = coverage.analyze(history.copy(), coverage_eval)
    return traceback_info, coverage_eval


def _get_contract_names():
    return set(
        i.contract_address for i in history if type(i.contract_address) is Contract and
        not i.contract_address._build['sourcePath'].startswith('<string')
    )
