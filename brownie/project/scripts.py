#!/usr/bin/python3
# mypy: disable-error-code="arg-type,union-attr"

import sys
import warnings
from ast import FunctionDef, Import, ImportFrom, dump, parse
from hashlib import sha1
from importlib import import_module, reload
from importlib.machinery import SourceFileLoader
from importlib.util import find_spec
from pathlib import Path, WindowsPath
from types import FunctionType, ModuleType
from typing import Any, Dict, Final, List, Optional, Sequence, Tuple

from brownie.exceptions import ProjectNotFound
from brownie.project.main import Project, check_for_project, get_loaded_projects
from brownie.utils import color

# C Constants

_FunctionDef: Final = FunctionDef
_Import: Final = Import
_ImportFrom: Final = ImportFrom

_Path: Final = Path

_FunctionType: Final = FunctionType

_parse: Final = parse
_dump: Final = dump

_sha1: Final = sha1

_import_module: Final = import_module
_find_spec: Final = find_spec
_reload: Final = reload

_DOT_PATH: Final = _Path(".")

_import_cache: Final[Dict[str, ModuleType]] = {}


def run(
    script_path: str,
    method_name: str = "main",
    args: Optional[Sequence[Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    project: Optional[Project] = None,
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
        args = ()
    if kwargs is None:
        kwargs = {}

    script, project = _get_path(script_path)

    # temporarily add project objects to the main namespace, so the script can import them
    if project is not None:
        project._add_to_main_namespace()

    # modify sys.path to ensure script can be imported
    if isinstance(script, WindowsPath):
        # far from elegant but just works
        root_path = str(_DOT_PATH.resolve())
        script = script.relative_to(_Path("..").resolve())
    else:
        root_path = _DOT_PATH.resolve().root

    sys.path.insert(0, root_path)

    try:
        module = _import_from_path(script)
        module_name = module.__name__

        func = getattr(module, method_name, None)
        if not isinstance(func, _FunctionType):
            raise AttributeError(f"Module '{module_name}' has no method '{method_name}'")

        file = module.__file__
        absolute_path = _Path(file)
        try:
            module_path = absolute_path.relative_to(_DOT_PATH.absolute())
        except ValueError:
            module_path = absolute_path
        print(
            f"\nRunning '{color('bright blue')}{module_path}{color}::"
            f"{color('bright cyan')}{method_name}{color}'..."
        )

        if not _include_frame:
            return func(*args, **kwargs)

        # this voodoo preserves the call frame of the function after it has finished executing.
        # we do this so that `brownie run -i` is able to drop into the console with the same
        # namespace as the function that it just ran.

        # first, we extract the source code from the function and parse it to an AST
        # we generate the AST from the entire module to preserve line numbers
        loader = module.__loader__
        assert isinstance(loader, SourceFileLoader)
        source = loader.get_source(module_name) or ""
        func_ast = _parse(source)

        # use the last function with the correct name, consistent with how python handles
        func_nodes: List = [
            i for i in func_ast.body if isinstance(i, _FunctionDef) and i.name == method_name
        ]
        func_ast.body = func_nodes[-1:]

        # next, we insert some new logic into the beginning of the function. this imports
        # the sys module and assigns the current frame to a global var `__brownie_frame`
        injected_source = "import sys\nglobal __brownie_frame\n__brownie_frame = sys._getframe()"
        injected_ast = _parse(injected_source)
        func_ast.body[0].body = injected_ast.body + func_ast.body[0].body  # type: ignore [attr-defined]

        # now we compile the AST into a code object, using the module's `__dict__` as our globals
        # so that we have access to all the required imports and other objects
        f_locals: Dict = module.__dict__.copy()
        del f_locals[method_name]
        func_code = compile(func_ast, file, "exec")
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
    path = _Path(path_str).with_suffix(".py")

    if not get_loaded_projects():
        if not path.exists():
            raise FileNotFoundError(f"Cannot find {path_str}")
        return path.resolve(), None

    if not path.is_absolute():
        for project in get_loaded_projects():
            project_structure: dict = project._structure
            project_scripts = project_structure["scripts"]
            if path.parts[:1] == (project_scripts,):
                script_path = project._path.joinpath(path)
            else:
                script_path = project._path.joinpath(project_scripts).joinpath(path)
            if script_path.exists():
                return script_path.resolve(), project
        raise FileNotFoundError(f"Cannot find {path_str}")

    if not path.exists():
        raise FileNotFoundError(f"Cannot find {path_str}")

    for project in get_loaded_projects():
        if path_str.startswith(project._path.as_posix()):
            return path.resolve(), project

    raise ProjectNotFound(f"{path_str} is not part of an active project")


def _import_from_path(path: Path) -> ModuleType:
    # Imports a module from the given path
    import_str = f"{'.'.join(path.parts[1:-1])}.{path.stem}"
    if import_str in _import_cache:
        _reload(_import_cache[import_str])
        return _import_cache[import_str]
    else:
        module = _import_module(import_str)
        _import_cache[import_str] = module
        return module


def _get_ast_hash(path: str) -> str:
    # Generates a hash based on the AST of a script.
    with _Path(path).open() as fp:
        ast_list = [_parse(fp.read(), path)]
    base_path = str(check_for_project(path))

    for obj in ast_list[0].body:
        if isinstance(obj, _Import):
            name = obj.names[0].name
        elif isinstance(obj, _ImportFrom):
            name = obj.module  # type: ignore [assignment]
        else:
            continue
        try:
            origin = _find_spec(name).origin
        except Exception:
            warnings.warn(
                f"{_Path(path).name}, unable to determine import spec for '{name}',"
                " the --update flag may not work correctly with this test file",
                ImportWarning,
            )
            continue
        if origin is not None and base_path in origin:
            with open(origin) as fp:
                ast_list.append(_parse(fp.read(), origin))

    dump = "\n".join(_dump(i) for i in ast_list)
    return _sha1(dump.encode()).hexdigest()
