#!/usr/bin/python3

from brownie.cli.utils import color
from . import (
    pathutils,
    loader,
    executor,
    coverage,
    output
)


def run_tests(test_path, only_update=True, check_coverage=False, gas_profile=False):
    '''Finds and runs tests for a project.

    test_path: path to locate tests in
    only_update: if True, will only run tests that were not previous run or where
                 changes to related files have occured
    check_coverage: if True, test coverage will also be evaluated
    gas_profile: if True, gas use data will be shown
    '''
    base_path = pathutils.check_for_project(test_path or ".")
    pathutils.check_build_hashes(base_path)
    pathutils.remove_empty_folders(base_path.joinpath('build/tests'))
    test_paths = pathutils.get_paths(test_path, "tests")
    if not executor.run_test_modules(test_paths, only_update, check_coverage, True):
        return
    if check_coverage:
        build_paths = pathutils.get_build_paths(test_paths)
        coverage_eval = coverage.merge_files(build_paths)
        output.coverage_totals(coverage_eval)
        pathutils.save_report(coverage_eval, base_path.joinpath("reports"))
    if gas_profile:
        output.gas_profile()


def run_script(script_path, method_name="main", args=(), kwargs={}, gas_profile=False):
    '''Loads a project script and runs a method in it.

    script_path: path of script to load
    method_name: name of method to run
    args: method args
    kwargs: method kwargs
    gas_profile: if True, gas use data will be shown

    Returns: return value from called method
    '''
    script_path = pathutils.get_path(script_path, "scripts")
    module = loader.import_from_path(script_path)
    if not hasattr(module, method_name):
        raise AttributeError(f"Module '{module.__name__}' has no method '{method_name}'")
    print(
        f"\nRunning '{color['module']}{module.__name__}{color}."
        f"{color['callable']}{method_name}{color}'..."
    )
    result = getattr(module, method_name)(*args, **kwargs)
    if gas_profile:
        output.gas_profile()
    return result
