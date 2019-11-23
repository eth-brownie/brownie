#!/usr/bin/python3

import ast
import importlib
import sys
from hashlib import sha1
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Optional, Tuple

from brownie.exceptions import ProjectNotFound
from brownie.project.main import Project, check_for_project, get_loaded_projects
from brownie.utils import color

_import_cache: Dict = {}


def run(
    script_path: str,
    method_name: str = "main",
    args: Optional[Tuple] = None,
    kwargs: Optional[Dict] = None,
    project: Any = None,
) -> None:
    """Loads a project script and runs a method in it.

    script_path: path of script to load
    method_name: name of method to run
    args: method args
    kwargs: method kwargs
    project: (deprecated)

    Returns: return value from called method
    """
    if args is None:
        args = tuple()
    if kwargs is None:
        kwargs = {}

    if not get_loaded_projects():
        raise ProjectNotFound("Cannot run a script without an active project")

    script, project = _get_path(script_path)

    # temporarily add project objects to the main namespace, so the script can import them
    brownie: Any = sys.modules["brownie"]
    brownie_dict = brownie.__dict__.copy()
    brownie_all = brownie.__all__.copy()
    brownie.__dict__.update(project)
    brownie.__all__.extend(project.__all__)

    try:
        script = script.absolute().relative_to(project._path)
        module = _import_from_path(script)

        name = module.__name__
        if not hasattr(module, method_name):
            raise AttributeError(f"Module '{name}' has no method '{method_name}'")
        print(
            f"\nRunning '{color['module']}{name}{color}.{color['callable']}{method_name}{color}'..."
        )
        return getattr(module, method_name)(*args, **kwargs)
    finally:
        # cleanup namespace
        brownie.__dict__.clear()
        brownie.__dict__.update(brownie_dict)
        brownie.__all__ = brownie_all


def _get_path(path_str: str) -> Tuple[Path, Project]:
    # Returns path to a python module
    path = Path(path_str).with_suffix(".py")

    if not path.is_absolute():
        if path.parts[0] != "scripts":
            path = Path("scripts").joinpath(path)
        for project in get_loaded_projects():
            if project._path.joinpath(path).exists():
                path = project._path.joinpath(path)
                return path, project
        raise FileNotFoundError(f"Cannot find {path_str}")

    if not path.exists():
        raise FileNotFoundError(f"Cannot find {path_str}")

    try:
        project = next(i for i in get_loaded_projects() if path_str.startswith(i._path.as_posix()))
    except StopIteration:
        raise ProjectNotFound(f"{path_str} is not part of an active project")

    return path, project


def _import_from_path(path: Path) -> ModuleType:
    # Imports a module from the given path
    import_str = ".".join(path.parts[:-1] + (path.stem,))
    if import_str in _import_cache:
        importlib.reload(_import_cache[import_str])
    else:
        _import_cache[import_str] = importlib.import_module(import_str)
    return _import_cache[import_str]


def _get_ast_hash(path: str) -> str:
    # Generates a hash based on the AST of a script.
    with Path(path).open() as fp:
        ast_list = [ast.parse(fp.read(), path)]
    base_path = str(check_for_project(path))
    for obj in [i for i in ast_list[0].body if type(i) in (ast.Import, ast.ImportFrom)]:
        if type(obj) is ast.Import:
            name = obj.names[0].name  # type: ignore
        else:
            name = obj.module  # type: ignore
        try:
            origin = importlib.util.find_spec(name).origin
        except Exception as e:
            raise type(e)(f"in {path} - {e}") from None
        if base_path in origin:
            with open(origin) as fp:
                ast_list.append(ast.parse(fp.read(), origin))
    dump = "\n".join(ast.dump(i) for i in ast_list)
    return sha1(dump.encode()).hexdigest()
