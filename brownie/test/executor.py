#!/usr/bin/python3

from requests.exceptions import ReadTimeout
import sys
import time

from . import pathutils, loader
from .output import TestPrinter
from brownie.network import history, rpc
from brownie.cli.utils import color, notify
from brownie._config import ARGV
from brownie.test import coverage
from brownie.exceptions import ExpectedFailing
import brownie.network as network
from brownie.network.contract import Contract


def run_test_modules(test_paths, only_update=True, check_coverage=False, save=True):
    '''Runs tests across one or more modules.

    Args:
        test_paths: list of test module paths
        only_update: if True, will only run tests that were not previous run or where
                     changes to related files have occured
        check_coverage: if True, test coverage will also be evaluated
        save: if True, results are saved in build/tests

    Returns: None
    '''
    test_data = _get_data(test_paths, only_update, check_coverage)
    if not test_data:
        if test_paths and only_update:
            notify("SUCCESS", "All test results are up to date.")
        else:
            notify("WARNING", "No tests were found.")
        return
    TestPrinter.set_grand_total(len(test_data))
    print("Running {} tests across {} module{}.".format(
        sum([len([x for x in i[2] if x[0].__name__ != "setup"]) for i in test_data]),
        len(test_data),
        "s" if len(test_data) > 1 else ""
    ))

    if not network.is_connected():
        network.connect()
    if check_coverage:
        ARGV['always_transact'] = True

    traceback_info = []
    start_time = time.time()
    try:
        for (test_path, old_coverage_eval, method_data) in test_data:
            tb, coverage_eval, contracts = _run_module(test_path, method_data, check_coverage)
            if tb:
                traceback_info += tb
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
            print()
            notify("SUCCESS", "All tests passed.")
        return True
    except KeyboardInterrupt:
        print("\n\nTest execution has been terminated by KeyboardInterrupt.")
        return False
    finally:
        if check_coverage:
            del ARGV['always_transact']
        print("\nTotal runtime: {:.4f}s".format(time.time() - start_time))
        if traceback_info:
            notify("WARNING", "{} test{} failed".format(
                len(traceback_info),
                "s" if len(traceback_info) > 1 else ""
            ))
            for err in traceback_info:
                print("\nTraceback for {0[0]}:\n{0[1]}".format(err))


def _get_data(test_paths, only_update, check_coverage):
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


def _run_module(test_path, method_data, check_coverage):
    rpc.reset()

    has_setup = method_data[0][0].__name__ == "setup"
    printer = TestPrinter(
        test_path,
        0 if has_setup else 1,
        len(method_data) - (1 if has_setup else 0)
    )

    coverage_eval = {}
    if has_setup:
        tb, coverage_eval = _run_method(*method_data[0], {}, printer, check_coverage)
        if tb:
            return tb, {}, set()
        del method_data[0]
    rpc.snapshot()
    traceback_info = []
    contracts = _get_contracts()

    for fn, args in method_data:
        history.clear()
        rpc.revert()
        tb, coverage_eval = _run_method(fn, args, coverage_eval, printer, check_coverage)
        contracts |= _get_contracts()
        traceback_info += tb
        if tb and tb[0][2] == ReadTimeout:
            raise ReadTimeout(
                "Timeout while communicating with RPC. Possibly the local client has crashed."
            )

    printer.finish()
    return traceback_info, coverage_eval, contracts


def _run_method(fn, args, coverage_eval, printer, check_coverage):
    desc = fn.__doc__ or fn.__name__
    if args['skip']:
        printer.skip(desc)
        return [], coverage_eval
    printer.start(desc)
    traceback_info, printer_args = [], []
    try:
        if check_coverage and 'always_transact' in args:
            ARGV['always_transact'] = args['always_transact']
        fn()
        if check_coverage:
            ARGV['always_transact'] = True
        if args['pending']:
            raise ExpectedFailing("Test was expected to fail")
    except Exception as e:
        printer_args = [e, args['pending']]
        if not args['pending'] or type(e) == ExpectedFailing:
            traceback_info = [(
                "{0[module]}{1.__module__}.{0[callable]}{1.__name__}{0}".format(color, fn),
                color.format_tb(sys.exc_info(), sys.modules[fn.__module__].__file__),
                type(e)
            )]
    if check_coverage:
        coverage_eval = coverage.analyze(history.copy(), coverage_eval)
    printer.stop(*printer_args)
    return traceback_info, coverage_eval


def _get_contracts():
    return set(
        i.contract_address for i in history if type(i.contract_address) is Contract and
        not i.contract_address._build['sourcePath'].startswith('<string')
    )
