#!/usr/bin/python3

from requests.exceptions import ReadTimeout
import sys
import time

from . import pathutils, loader
from .output import TestPrinter
from brownie.network import history, rpc
from brownie.cli.utils import color, notify
from brownie._config import ARGV, CONFIG
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
    count = sum([len([x for x in i[2] if x[0].__name__ != "setup"]) for i in test_data])
    print(f"Running {count} test{_s(count)} across {len(test_data)} module{_s(len(test_data))}.")

    if not network.is_connected():
        network.connect()
    if check_coverage:
        ARGV['always_transact'] = True

    traceback_info = []
    failed = 0
    start_time = time.time()
    try:
        for (test_path, old_coverage_eval, method_data) in test_data:
            tb, coverage_eval, contracts = _run_module(test_path, method_data, check_coverage)
            if tb:
                traceback_info += tb
                failed += 1
            if not save:
                continue

            contract_names = set(i._name for i in contracts)
            contract_names |= set(x for i in contracts for x in i._build['dependencies'])
            pathutils.save_build_json(
                test_path,
                "passing" if not tb else "failing",
                coverage_eval or old_coverage_eval,
                contract_names
            )

        if not traceback_info:
            print()
            notify("SUCCESS", "All tests passed.")
            return True
        return False
    except KeyboardInterrupt:
        print("\n\nTest execution has been terminated by KeyboardInterrupt.")
        return
    finally:
        if check_coverage:
            del ARGV['always_transact']
        print(f"\nTotal runtime: {time.time() - start_time:.4f}s")
        if traceback_info:
            count = len(traceback_info)
            notify("WARNING", f"{count} test{_s(count)} failed in {failed} module{_s(failed)}.")
            for err in traceback_info:
                print(f"\nTraceback for {err[0]}:\n{err[1]}")


def _get_data(test_paths, only_update, check_coverage):
    test_data = []
    for path in test_paths:
        build_json = pathutils.get_build_json(path)
        if (
            only_update and build_json['result'] == "passing" and
            (build_json['coverage'] or not check_coverage)
        ):
            continue
        fn_list = loader.get_methods(path, check_coverage)
        if not fn_list:
            continue
        # test path, build data, list of (fn, args)
        test_data.append((path, build_json['coverage'], fn_list))
    return test_data


def _run_module(test_path, method_data, check_coverage):
    rpc.reset()

    has_setup = method_data[0][0].__name__ == "setup"
    printer = TestPrinter(
        str(test_path).replace(CONFIG['folders']['project'], "."),
        0 if has_setup else 1,
        len(method_data) - (1 if has_setup else 0)
    )

    coverage_eval = {}
    if has_setup:
        tb, coverage_eval = _run_method(*method_data[0], {}, printer, check_coverage)
        if tb:
            printer.finish()
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
                f"{color['module']}{fn.__module__}.{color['callable']}{fn.__name__}{color}",
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


def _s(count):
    return "s" if count != 1 else ""
