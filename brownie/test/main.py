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
    # TODO apply range
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


# TODO
# def apply_range(test_data, idx):
#     test_names = list(test_data[0][-1])
#     if "0" in idx:
#         sys.exit(ERROR+"Range cannot include 0. First test is 1.")
#     idx = [i-1 if i > 0 else i for i in (int(x) for x in idx.split(':'))]
#     if len(idx) > 1:
#         if (min(idx+[0]), max(idx+[0])).count(0) != 1:
#             sys.exit(ERROR+"Range must be entirely positive or negative.")
#     idx = slice(*idx) if len(idx) > 1 else idx[0]
#     try:
#         if 'setup' in test_names:
#             test_names.remove('setup')
#             test_names = ['setup'] + ([test_names[idx]] if type(idx) is int else test_names[idx])
#         else:
#             test_names = [test_names[idx]] if type(idx) is int else test_names[idx]
#         return [list(test_data[0][:-1])+[test_names]]
#     except IndexError:
#         sys.exit(ERROR+"Invalid range. Must be an integer or slice (eg. 1:4)")
