#!/usr/bin/python3

import ast
from hashlib import sha1
import importlib
import json
import os
from pathlib import Path
import sys
import time

from . import coverage
from brownie.project import build, check_for_project


def check_build_hashes(base_path):
    '''Checks the hash data in all test build json files, and deletes those where
    hashes have changed.

    Args:
        base_path: root path of project to check

    Returns: None'''
    base_path = Path(base_path)
    build_path = base_path.joinpath('build/tests')
    for coverage_json in list(build_path.glob('**/*.json')):
        try:
            with coverage_json.open() as f:
                dependents = json.load(f)['sha1']
        except json.JSONDecodeError:
            coverage_json.unlink()
            continue
        for path, hash_ in dependents.items():
            path = base_path.joinpath(path)
            if path.exists():
                if path.suffix != ".json":
                    if get_ast_hash(path) == hash_:
                        continue
                elif build.get(path.stem)['bytecodeSha1'] == hash_:
                    continue
            coverage_json.unlink()
            break


def remove_empty_folders(base_path):
    '''Removes empty subfolders within the given path.'''
    for path in [Path(i[0]) for i in list(os.walk(base_path))[:0:-1]]:
        if not list(path.glob('*')):
            path.rmdir()


def get_ast_hash(path):
    '''Generates a hash based on the AST of a script.

    Args:
        path: path of the script to hash

    Returns: sha1 hash as bytes'''
    with Path(path).open() as f:
        ast_list = [ast.parse(f.read(), path)]
    base_path = str(check_for_project(path))
    for obj in [i for i in ast_list[0].body if type(i) in (ast.Import, ast.ImportFrom)]:
        if type(obj) is ast.Import:
            name = obj.names[0].name
        else:
            name = obj.module
        origin = importlib.util.find_spec(name).origin
        if base_path in origin:
            with open(origin) as f:
                ast_list.append(ast.parse(f.read(), origin))
    dump = "\n".join(ast.dump(i) for i in ast_list)
    return sha1(dump.encode()).hexdigest()


def get_path(path_str, default_folder="scripts"):
    '''Returns path to a python module.

    Args:
        path_str: module path
        default_folder: default folder path to check if path_str is not found

    Returns: Path object'''
    if not path_str.endswith('.py'):
        path_str += ".py"
    path = _get_path(path_str, default_folder)
    if not path.is_file():
        raise FileNotFoundError("{} is not a file".format(path_str))
    return path


def get_paths(path_str=None, default_folder="tests"):
    '''Returns paths to python modules.

    Args:
        path_str: base path to look for modules in
        default_folder: default folder path to check if path_str is not found

    Returns: list of Path objects'''
    path = _get_path(path_str, default_folder)
    if not path.is_dir():
        return [path]
    return [i for i in path.absolute().glob('**/[!_]*.py') if "/_" not in str(i)]


def _get_path(path_str, default_folder):
    path = Path(path_str or default_folder)
    if not path.exists() and not path.is_absolute():
        if not path_str.startswith(default_folder+'/'):
            path = Path(default_folder).joinpath(path_str)
        if not path.exists() and sys.path[0]:
            path = Path(sys.path[0]).joinpath(path)
    if not path.exists():
        raise FileNotFoundError("Cannot find {}".format(path_str))
    if path.is_file() and path.suffix != ".py":
        raise TypeError("'{}' is not a python script".format(path_str))
    return path


def get_build_paths(test_paths):
    '''Given a list of test paths, returns an equivalent list of build paths'''
    base_path = check_for_project(test_paths[0])
    build_path = base_path.joinpath('build')
    test_paths = [Path(i).absolute().with_suffix('.json') for i in test_paths]
    return [build_path.joinpath(i.relative_to(base_path)) for i in test_paths]


def get_build_json(test_path):
    '''Loads the result data for a given test. If the file cannot be found or is
    corrupted, creates the necessary folder structure and returns an appropriately
    formatted dict.

    Args:
        test_path: path to the test file

    Returns: loaded build data as a dict'''
    build_path = get_build_paths([test_path])[0]
    if build_path.exists():
        try:
            with build_path.open() as f:
                return json.load(f)
        except json.JSONDecodeError:
            build_path.unlink()
    for path in list(build_path.parents)[::-1]:
        path.mkdir(exist_ok=True)
    return {'result': None, 'coverage': {}, 'sha1': {}}


def save_build_json(module_path, result, coverage_eval, contract_names):
    '''
    Saves the result data for a given test.

    Args:
        module_path: path of the test module
        result: result of test execution (passing / failing)
        coverage_eval: coverage evaluation as a dict
        contract_names: list of contracts called by the test

    Returns: None'''
    module_path = Path(module_path).absolute()
    project_path = check_for_project(module_path)
    build_path = get_build_paths([module_path])[0]
    build_files = [Path('build/contracts/{}.json'.format(i)) for i in contract_names]
    build_json = {
        'result': result,
        'coverage': coverage_eval,
        'sha1': dict((str(i), build.get(i.stem)['bytecodeSha1']) for i in build_files)
    }
    path = str(module_path.relative_to(project_path))
    build_json['sha1'][path] = get_ast_hash(module_path)
    with build_path.open('w') as f:
        json.dump(build_json, f, sort_keys=True, indent=2, default=sorted)


def save_report(coverage_eval, report_path):
    '''Saves a test coverage report for viewing in the GUI.

    Args:
        coverage_eval: Coverage evaluation dict
        report_path: Path to save to. If a folder is given, saves as coverage-ddmmyy

    Returns: Path object where report file was saved'''
    report = {
        'highlights': coverage.get_highlights(coverage_eval),
        'coverage': coverage.get_totals(coverage_eval),
        'sha1': {}  # TODO
    }
    report_path = Path(report_path).absolute()
    if report_path.is_dir():
        filename = "coverage-"+time.strftime('%d%m%y')+"{}.json"
        count = len(list(report_path.glob(filename.format('*'))))
        report_path = report_path.joinpath(filename.format("-"+str(count) if count else ""))
    with report_path.open('w') as f:
        json.dump(report, f, sort_keys=True, indent=2, default=sorted)
    print("\nCoverage report saved at {}".format(report_path.relative_to(sys.path[0])))
    return report_path
