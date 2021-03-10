#!/usr/bin/python3

import ast
import importlib
import inspect
import sys
import warnings
from hashlib import sha1
from inspect import getmembers, isfunction
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Generator, Optional, Tuple

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
    _include_frame: bool = False,
) -> Any:
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
    # modify sys.path to ensure script can be imported
    root_path = Path(".").resolve().root
    sys.path.insert(0, root_path)

    script, project = _get_path(script_path)

    # temporarily add project objects to the main namespace, so the script can import them
    if project is not None:
        project._add_to_main_namespace()

    try:
        module = _import_from_path(script)

        name = module.__name__

        if not hasattr(module, method_name):
            module_methods = get_method_list(module)
            available_methods_string = ""
            for method in module_methods:
                available_methods_string += (
                    f"{color('green')}{method[0]}{color} brownie run {script_path} {method[0]}\n"
                )

            raise AttributeError(
                f"Module '{name}' has no method '{method_name}'\n"
                f"Available methods:\n"
                f"{available_methods_string}"
            )
        try:
            module_path = Path(module.__file__).relative_to(Path(".").absolute())
        except ValueError:
            module_path = Path(module.__file__)
        print(
            f"\nRunning '{color('bright blue')}{module_path}{color}::"
            f"{color('bright cyan')}{method_name}{color}'..."
        )
        func = getattr(module, method_name)
        if not _include_frame:
            return func(*args, **kwargs)

        # this voodoo preserves the call frame of the function after it has finished executing.
        # we do this so that `brownie run -i` is able to drop into the console with the same
        # namespace as the function that it just ran.

        # first, we extract the source code from the function and parse it to an AST
        source = inspect.getsource(func)
        func_ast = ast.parse(source)

        # next, we insert some new logic into the beginning of the function. this imports
        # the sys module and assigns the current frame to a global var `__brownie_frame`
        injected_source = "import sys\nglobal __brownie_frame\n__brownie_frame = sys._getframe()"
        injected_ast = ast.parse(injected_source)
        func_ast.body[0].body = injected_ast.body + func_ast.body[0].body  # type: ignore

        # now we compile the AST into a code object, using the module's `__dict__` as our globals
        # so that we have access to all the required imports and other objects
        f_locals: Dict = module.__dict__.copy()
        del f_locals[method_name]
        func_code = compile(func_ast, "", "exec")
        exec(func_code, f_locals)

        # finally, we execute our new function from inside the copied globals dict. the frame
        # is added to the dict as `__global_frame` per our injected code, and we return it for
        # use within the console. so simple!
        return_value = f_locals[method_name](*args, **kwargs)
        return return_value, f_locals["__brownie_frame"]

    finally:
        # cleanup namespace and sys.path
        sys.path.remove(root_path)
        if project is not None:
            project._remove_from_main_namespace()


def _get_path(path_str: str) -> Tuple[Path, Optional[Project]]:
    # Returns path to a python module
    root_path = Path(".").resolve().root
    # modify sys.path to ensure script can be imported
    sys.path.insert(0, root_path)
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
        string_tree = create_string_tree("scripts")
        raise FileNotFoundError(
            f"Cannot find {path_str}\n" f"Available scripts:\n" f"{string_tree}"
        )

    if not path.exists():
        string_tree = create_string_tree("scripts")
        raise FileNotFoundError(
            f"Cannot find {path_str}\n" f"Available scripts:\n" f"{string_tree}"
        )

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


def get_method_list(module: ModuleType) -> list:
    methods = [
        method
        for method in getmembers(module)
        if isfunction(method[1]) and not method[0].startswith("_")
    ]
    return methods


space = "    "
branch = "│   "
tee = "├── "
last = "└── "


def tree(dir_path: Path, prefix: str = "") -> Generator:
    # A recursive generator from https://stackoverflow.com/a/59109706
    contents = list(dir_path.iterdir())
    contents = list(filter(lambda path: not path.name.startswith("__"), contents))

    pointers = [tee] * (len(contents) - 1) + [last]

    for pointer, path in zip(pointers, contents):
        if path.name.endswith(".py"):
            try:

                module = _import_from_path(path.absolute())
                method_list = get_method_list(module)
                if len(method_list) == 0:
                    yield prefix + pointer + path.name + "    No available methods"
                else:
                    yield prefix + pointer + path.name

                    extension = branch if pointer == tee else space
                    for i in range(len(method_list)):
                        method_prefix = last if i == len(method_list) - 1 else tee
                        method_name = method_list[i][0]
                        full_prefix = prefix + extension + method_prefix
                        colored_method = f'{color("green")}{method_name}{color}'
                        command = "    brownie run " + path.as_posix()[:-3] + " " + method_name
                        yield full_prefix + colored_method + command

            except Exception:
                path_with_prefix = prefix + pointer + path.name
                yield path_with_prefix + f'{color("red")}    Error while importing a module{color}'

        if path.is_dir():
            yield prefix + pointer + path.name
            extension = branch if pointer == tee else space
            yield from tree(path, prefix=prefix + extension)


def create_string_tree(path_name: str) -> str:
    string_tree = ""
    tree_generator = tree(Path(path_name))
    for line in tree_generator:
        string_tree += line + "\n"
    return string_tree
