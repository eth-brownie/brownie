#!/usr/bin/python3

import ast
from hashlib import sha1
import importlib
import json
import os
from pathlib import Path
import sys

from brownie.project import build, check_for_project


def check_build_hashes(base_path):
    '''Checks the hash data in all test build json files, and deletes those where
    hashes have changed.

    Args:
        base_path: root path of project to check

    Returns: None'''
    build_path = Path(base_path).joinpath('build/tests')
    for coverage_json in list(build_path.glob('**/*.json')):
        try:
            dependents = json.load(coverage_json.open())['sha1']
        except json.JSONDecodeError:
            coverage_json.unlink()
            continue
        for path, hash_ in dependents.items():
            path = Path(path)
            if path.exists():
                if path.suffix != ".json":
                    if get_ast_hash(path) == hash_:
                        continue
                elif build.get(path.stem)['bytecodeSha1'] == hash_:
                    continue
            coverage_json.unlink()
            break


def remove_empty_folders(base_path):
    # remove empty folders
    for path in [Path(i[0]) for i in list(os.walk(base_path))[:0:-1]]:
        if not list(path.glob('*')):
            path.rmdir()


def get_ast_hash(path):
    '''Generates a hash based on the AST of a script.

    Args:
        path: path of the script to hash

    Returns: sha1 hash as bytes'''
    ast_list = [ast.parse(Path(path).open().read())]
    base_path = str(check_for_project(path))
    for obj in [i for i in ast_list[0].body if type(i) in (ast.Import, ast.ImportFrom)]:
        if type(obj) is ast.Import:
            name = obj.names[0].name
        else:
            name = obj.module
        origin = importlib.util.find_spec(name).origin
        if base_path in origin:
            ast_list.append(ast.parse(open(origin).read()))
    dump = "\n".join(ast.dump(i) for i in ast_list)
    return sha1(dump.encode()).hexdigest()


def get_paths(path_str=None):
    '''Returns the absolute path to every test file within the given path.'''
    path = Path(path_str or "tests")
    if not path.exists() and not path.absolute():
        if not path_str.startswith('tests/'):
            path = Path('tests').joinpath(path_str)
        if not path.exists() and sys.path[0]:
            path = Path(sys.path[0]).joinpath(path)
    if not path.exists():
        raise FileNotFoundError("Cannot find {}".format(path_str))
    if not path.is_dir():
        return [path]
    return [i for i in path.absolute().glob('**/[!_]*.py') if "/_" not in str(i)]


def get_build_paths(test_paths):
    '''Given a list of test paths, returns an equivalent list of build paths'''
    base_path = check_for_project(test_paths[0])
    build_path = base_path.joinpath('build')
    test_paths = [i.with_suffix('.json') for i in test_paths]
    return [build_path.joinpath(i.relative_to(base_path)) for i in test_paths]


def get_build_json(test_path):
    '''Loads the result data for a given test. If the file cannot be found or is
    corrupted, creates the necessary folder structure and returns an appropriately
    formatted dict.

    Args:
        test_path: path to the test file

    Returns:
        build_path: path to the build data file
        build_json: loaded build data as a dict'''
    build_path = get_build_paths([test_path])[0]
    if build_path.exists():
        try:
            return build_path, json.load(build_path.open())
        except json.JSONDecodeError:
            build_path.unlink()
    for path in list(build_path.parents)[::-1]:
        path.mkdir(exist_ok=True)
    return build_path, {'tests': [], 'coverage': {}, 'sha1': {}}


def save_build_json(module_path, build_path, coverage_eval, contract_names):
    '''
    Saves the result data for a given test.

    Args:
        module_path: path of the test module
        build_path: path to save the build data at
        coverage_eval: coverage evaluation as a dict
        contract_names: list of contracts called by the test

    Returns: None'''
    project_path = check_for_project(module_path)
    build_files = [Path('build/contracts/{}.json'.format(i)) for i in contract_names]
    build_json = {
        'tests': [],
        'coverage': coverage_eval,
        'sha1': dict((str(i), build.get(i.stem)['bytecodeSha1']) for i in build_files)
    }
    path = str(Path(module_path).relative_to(project_path))
    build_json['sha1'][path] = get_ast_hash(module_path)
    json.dump(
        build_json,
        build_path.open('w'),
        sort_keys=True,
        indent=2,
        default=sorted
    )
