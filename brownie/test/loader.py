#!/usr/bin/python3

import ast
from hashlib import sha1
import importlib
import json
import os
from pathlib import Path
import sys

from brownie.project import build
from brownie.types import FalseyDict


def check_build_hashes(base_path):
    '''Checks the hash data in all test build json files, and deletes those where
    hashes have changed.'''
    coverage_path = Path(base_path).joinpath('build/tests')
    for coverage_json in list(coverage_path.glob('**/*.json')):
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

    # remove empty folders
    for path in [Path(i[0]) for i in list(os.walk(base_path))[:0:-1]]:
        if not list(path.glob('*')):
            path.rmdir()


def get_paths(path_str="tests"):
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


def get_build_json(base_path, test_path):
    '''
    Loads the build data for a given test. If the file cannot be found or is corrupted,
    creates the necessary folder structure and returns an appropriately formatted dict.

    Args:
        base_path: base project path
        test_path: path to the test file

    Returns:
        build_path: path to the build data file
        build_json: loaded build data as a dict'''
    build_path = Path(base_path).joinpath('build/').joinpath(test_path.relative_to(base_path))
    if build_path.exists():
        try:
            return build_path, json.load(build_path.open())
        except json.JSONDecodeError:
            build_path.unlink()
    for path in list(build_path.parents)[::-1]:
        path.mkdir(exist_ok=True)
    return build_path, {'tests': [], 'coverage': {}, 'sha1': {}}


def get_ast_hash(path):
    ast_list = [ast.parse(Path(path).open().read())]
    base_path = str(Path(sys.path[0]).absolute())
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


def get_methods(path, coverage=False):
    '''Parses a test module and returns information about the test methods.

    Args:
        path: path to the module
        coverage: is coverage analysis enabled?

    Returns:
        List of tuples as [('method name', {kwarg: value}) .. ]
    '''
    source = Path(path).open().read()
    node = ast.parse(source)
    fn_nodes = [i for i in node.body if type(i) is ast.FunctionDef and not i.name.startswith('_')]

    # check for duplicate names
    if len(fn_nodes) != len(set(fn_nodes)):
        duplicates = set(i for i in fn_nodes if fn_nodes.count(i) > 1)
        raise ValueError(
            "{}: multiple methods of same name - {}".format(path.name, ", ".join(duplicates))
        )

    setup_fn = next((i for i in fn_nodes if i.name == "setup"), False)
    if setup_fn:
        default_args = _get_args(setup_fn, {}, coverage)
        if 'skip' in default_args and default_args['skip']:
            return []
        fn_nodes.remove(setup_fn)
        fn_nodes.insert(0, setup_fn)
    else:
        default_args = {}
    return [(i.name, _get_args(i, default_args, coverage)) for i in fn_nodes]


def _get_args(node, defaults={}, coverage=False):
    args = dict((
        node.args.args[i].arg,
        _coverage_to_bool(node.defaults[i].value, coverage)
    ) for i in range(len(list(node.args.args))))
    return FalseyDict({**defaults, **args})


def _coverage_to_bool(value, coverage):
    return value if value != "coverage" else coverage


def import_module(test_path):
    path = test_path.relative_to(sys.path[0])
    import_str = ".".join(path.parts[:-1]+(path.stem,))
    return importlib.import_module(import_str)
