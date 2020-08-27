#!/usr/bin/python3

import ast
import importlib
import sys
import warnings
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

    script, project = _get_path(script_path)

    # temporarily add project objects to the main namespace, so the script can import them
    if project is not None:
        project._add_to_main_namespace()

    # modify sys.path to ensure script can be imported
    root_path = Path(".").resolve().root
    sys.path.insert(0, root_path)

    try:
        module = _import_from_path(script)

        name = module.__name__

        if not hasattr(module, method_name):
            raise AttributeError(f"Module '{name}' has no method '{method_name}'")
        try:
            module_path = Path(module.__file__).relative_to(Path(".").absolute())
        except ValueError:
            module_path = Path(module.__file__)
        print(
            f"\nRunning '{color('bright blue')}{module_path}{color}::"
            f"{color('bright cyan')}{method_name}{color}'..."
        )
        return getattr(module, method_name)(*args, **kwargs)
    finally:
        # cleanup namespace and sys.path
        sys.path.remove(root_path)
        if project is not None:
            project._remove_from_main_namespace()


def _get_path(path_str: str) -> Tuple[Path, Optional[Project]]:
    # Returns path to a python module
    path = Path(path_str).with_suffix(".py")

    if not get_loaded_projects():
        if not path.exists():
            raise FileNotFoundError(f"Cannot find {path_str}")
        return path.resolve(), None

    if not path.is_absolute():
        for project in get_loaded_projects():
            if path.parts[:1] == (project._structure["scripts"],):
                script_path = project._path.joinpath(path)
            else:
                script_path = project._path.joinpath(project._structure["scripts"]).joinpath(path)
            if script_path.exists():
                return script_path.resolve(), project
        raise FileNotFoundError(f"Cannot find {path_str}")

    if not path.exists():
        raise FileNotFoundError(f"Cannot find {path_str}")

    try:
        project = next(i for i in get_loaded_projects() if path_str.startswith(i._path.as_posix()))
    except StopIteration:
        raise ProjectNotFound(f"{path_str} is not part of an active project")

    return path.resolve(), project


def _import_from_path(path: Path) -> ModuleType:
    # Imports a module from the given path
    import_str = ".".join(path.parts[1:-1] + (path.stem,))
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

    for obj in [i for i in ast_list[0].body if isinstance(i, (ast.Import, ast.ImportFrom))]:
        if isinstance(obj, ast.Import):
            name = obj.names[0].name  # type: ignore
        else:
            name = obj.module  # type: ignore
        try:
            origin = importlib.util.find_spec(name).origin  # type: ignore
        except Exception:
            warnings.warn(
                f"{Path(path).name}, unable to determine import spec for '{name}',"
                " the --update flag may not work correctly with this test file",
                ImportWarning,
            )
            continue
        if origin is not None and base_path in origin:
            with open(origin) as fp:
                ast_list.append(ast.parse(fp.read(), origin))

    dump = "\n".join(ast.dump(i) for i in ast_list)
    return sha1(dump.encode()).hexdigest()
