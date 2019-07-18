#!/usr/bin/python3

import ast
from hashlib import sha1
import importlib
from pathlib import Path
import sys

from brownie.cli.utils import color
from brownie.test.output import print_gas_profile
from brownie.project import check_for_project


def run(script_path, method_name="main", args=None, kwargs=None, gas_profile=False):
    '''Loads a project script and runs a method in it.

    script_path: path of script to load
    method_name: name of method to run
    args: method args
    kwargs: method kwargs
    gas_profile: if True, gas use data will be shown

    Returns: return value from called method
    '''
    if args is None:
        args = tuple()
    if kwargs is None:
        kwargs = {}
    script_path = _get_path(script_path, "scripts")
    module = _import_from_path(script_path)
    name = module.__name__
    if not hasattr(module, method_name):
        raise AttributeError(f"Module '{name}' has no method '{method_name}'")
    print(
        f"\nRunning '{color['module']}{name}{color}.{color['callable']}{method_name}{color}'..."
    )
    result = getattr(module, method_name)(*args, **kwargs)
    if gas_profile:
        print_gas_profile()
    return result


def _get_path(path_str, default_folder="scripts"):
    '''Returns path to a python module.

    Args:
        path_str: module path
        default_folder: default folder path to check if path_str is not found

    Returns: Path object'''
    if not path_str.endswith('.py'):
        path_str += ".py"
    path = Path(path_str)
    if not path.exists() and not path.is_absolute():
        if not path_str.startswith(default_folder+'/'):
            path = Path(default_folder).joinpath(path_str)
        if not path.exists() and sys.path[0]:
            path = Path(sys.path[0]).joinpath(path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot find {path_str}")
    if not path.is_file():
        raise FileNotFoundError(f"{path_str} is not a file")
    if path.suffix != ".py":
        raise TypeError(f"'{path_str}' is not a python script")
    return path


def _import_from_path(path):
    '''Imports a module from the given path.'''
    path = Path(path).absolute().relative_to(sys.path[0])
    import_str = ".".join(path.parts[:-1]+(path.stem,))
    return importlib.import_module(import_str)


def get_ast_hash(path):
    '''Generates a hash based on the AST of a script.

    Args:
        path: path of the script to hash

    Returns: sha1 hash as bytes'''
    with Path(path).open() as fp:
        ast_list = [ast.parse(fp.read(), path)]
    base_path = str(check_for_project(path))
    for obj in [i for i in ast_list[0].body if type(i) in (ast.Import, ast.ImportFrom)]:
        if type(obj) is ast.Import:
            name = obj.names[0].name
        else:
            name = obj.module
        origin = importlib.util.find_spec(name).origin
        if base_path in origin:
            with open(origin) as fp:
                ast_list.append(ast.parse(fp.read(), origin))
    dump = "\n".join(ast.dump(i) for i in ast_list)
    return sha1(dump.encode()).hexdigest()
