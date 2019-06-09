#!/usr/bin/python3

from pathlib import Path

from . import (
    pathutils,
    executor,
    coverage,
    output
)


def run_tests(base_path, test_path, only_update=True, check_coverage=False, gas_profile=False):
    '''Finds and runs tests for a project.

    base_path: brownie project path
    test_path: path to locate tests in
    only_update: if True, will only run tests that were not previous run or where
                 changes to related files have occured
    check_coverage: if True, test coverage will also be evaluated
    gas_profile: if True, gas use data will be shown
    '''
    base_path = Path(base_path)
    pathutils.check_build_hashes(base_path)
    pathutils.remove_empty_folders(base_path.joinpath('build/tests'))
    test_paths = pathutils.get_paths(test_path)
    if not executor.run_test_modules(test_paths, only_update, check_coverage, True):
        return
    if check_coverage:
        build_paths = pathutils.get_build_paths(test_paths)
        coverage_eval = coverage.merge_files(build_paths)
        output.coverage_totals(coverage_eval)
        pathutils.save_report(coverage_eval, base_path.joinpath("reports"))
    if gas_profile:
        output.gas_profile()


# cli.run
# def run_script(base_path, script_path, method_name="main")
