#!/usr/bin/python3

from pathlib import Path

from . import (
    pathutils,
    loader,
    executor,
    coverage,
    output
)


def run_tests(base_path, test_path, update=True, cov=False, gas_profile=False):
    '''Finds and runs tests for a project.

    base_path: brownie project path
    test_path: path to locate tests in
    update: if True, will only run tests that were not previous run or where changes
            to related files have occured
    cov: if True, test coverage will also be evaluated
    gas_profile: if True, gas use data will be shown
    '''
    base_path = Path(base_path)
    pathutils.check_build_hashes(base_path)
    pathutils.remove_empty_folders(base_path.joinpath('build/tests'))
    test_paths = pathutils.get_paths(test_path)
    build_paths, test_data = _get_test_data(test_paths, update, cov)
    if test_data:
        executor.run_test_modules(test_data, True)
    if cov:
        coverage_eval = coverage.merge_files(build_paths)
        output.coverage_totals(coverage_eval)
        pathutils.save_report(coverage_eval, base_path.joinpath("reports"))
    if gas_profile:
        output.gas_profile()


# cli.run
# def run_script(base_path, script_path, method_name="main")


def _get_test_data(test_paths, update, coverage):
    build_paths, test_data = [], []
    for path in test_paths:
        build_path, build_json = pathutils.get_build_json(path)
        build_paths.append(build_path)
        if build_json['sha1'] and update:
            continue
        fn_list = loader.get_methods(path, coverage)
        if not fn_list:
            continue
        module = loader.import_from_path(path)
        fn_list = [(getattr(module, i[0]), i[1]) for i in fn_list]
        # imported module, path to build file, build data, list of (fn, args)
        test_data.append((module, build_path, build_json, fn_list))
    return build_paths, test_data
