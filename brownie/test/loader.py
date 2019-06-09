#!/usr/bin/python3

import ast
import importlib
from pathlib import Path
import sys

from brownie.types import FalseyDict


def import_from_path(path):
    '''Imports a module from the given path.'''
    path = Path(path).absolute().relative_to(sys.path[0])
    import_str = ".".join(path.parts[:-1]+(path.stem,))
    return importlib.import_module(import_str)


def get_methods(path, coverage=False):
    '''Parses a module and returns information about the methods it contains.

    Args:
        path: path to the module
        coverage: is coverage analysis enabled?

    Returns:
        List of tuples as [(method, FalseyDict({'arg': value}), ) .. ] '''
    source = Path(path).open().read()
    node = ast.parse(source)
    fn_nodes = [i for i in node.body if type(i) is ast.FunctionDef and not i.name.startswith('_')]

    if not fn_nodes:
        return []

    # check for duplicate names
    if len(fn_nodes) != len(set(fn_nodes)):
        duplicates = set(i for i in fn_nodes if fn_nodes.count(i) > 1)
        raise ValueError(
            "{}: multiple methods of same name - {}".format(path.name, ", ".join(duplicates))
        )

    default_args = {}
    setup_fn = next((i for i in fn_nodes if i.name == "setup"), False)
    if setup_fn:
        # apply default arguments across all methods in the module
        default_args = _get_args(setup_fn, {}, coverage)
        if 'skip' in default_args and default_args['skip']:
            return []
        fn_nodes.remove(setup_fn)
        fn_nodes.insert(0, setup_fn)
    module = import_from_path(path)
    return [(getattr(module, i.name), _get_args(i, default_args, coverage)) for i in fn_nodes]


def _get_args(node, defaults={}, coverage=False):
    args = dict((
        node.args.args[i].arg,
        _coverage_to_bool(node.args.defaults[i], coverage)
    ) for i in range(len(list(node.args.args))))
    return FalseyDict({**defaults, **args})


def _coverage_to_bool(node, coverage):
    value = getattr(node, node._fields[0])
    return value if value != "coverage" else coverage
