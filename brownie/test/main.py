#!/usr/bin/python3

from pathlib import Path

from . import loader, executor, output


def run_tests(base_path, test_path, update=True, coverage=False, gas_profile=False):
    base_path = Path(base_path)
    loader.check_build_hashes(base_path)
    test_paths = loader.get_paths(test_path)
    build_paths, test_data = _get_test_data(base_path, test_paths, update, coverage)
    # apply range
    executor.run_test_modules(test_data, True)
    if coverage:
        output.display_report(build_paths, base_path.joinpath("reports"))
    if gas_profile:
        output.display_gas_profile()


def _get_test_data(base_path, test_paths, update, coverage):
    build_paths, test_data = [], []
    for path in test_paths:
        build_path, build_json = loader.get_build_json(base_path, path)
        build_paths.append(build_path)
        if build_json['sha1'] and update:
            continue
        fn_list = loader.get_methods(path, coverage)
        if not fn_list:
            continue
        module = loader.import_module(path)
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
