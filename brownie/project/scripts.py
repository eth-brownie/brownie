#!/usr/bin/python3
# mypy: disable-error-code="arg-type,attr-defined,union-attr"

import pathlib
import sys
import warnings
from ast import (
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Delete,
    FunctionDef,
    Import,
    ImportFrom,
    Lambda,
    Name,
    dump,
    parse,
)
from collections.abc import Iterator, Sequence
from importlib import reload
from importlib.machinery import SourceFileLoader
from importlib.util import find_spec
from pathlib import WindowsPath
from types import FunctionType, ModuleType
from typing import Any, Final

from brownie._c_constants import Path, import_module, sha1
from brownie._config import _load_project_structure_config
from brownie.exceptions import ProjectNotFound
from brownie.project.main import Project, check_for_project, get_loaded_projects
from brownie.utils import color
from brownie.utils._color import bright_blue, bright_cyan

# C Constants

_FunctionDef: Final = FunctionDef
_AsyncFunctionDef: Final = AsyncFunctionDef
_Assign: Final = Assign
_AnnAssign: Final = AnnAssign
_Delete: Final = Delete
_Name: Final = Name
_Lambda: Final = Lambda
_Import: Final = Import
_ImportFrom: Final = ImportFrom

_FunctionType: Final = FunctionType

_parse: Final = parse
_dump: Final = dump

_import_module: Final = import_module
_find_spec: Final = find_spec
_reload: Final = reload

_DOT_PATH: Final = Path(".")

_import_cache: Final[dict[str, ModuleType]] = {}


def run(
    script_path: str,
    method_name: str = "main",
    args: Sequence[Any] | None = None,
    kwargs: dict[str, Any] | None = None,
    project: Project | None = None,
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
        script = script.relative_to(Path("..").resolve())
    else:
        root_path = _DOT_PATH.resolve().root

    sys.path.insert(0, root_path)

    try:
        module = _import_from_path(script)
        module_name = module.__name__

        func = getattr(module, method_name, None)
        if not isinstance(func, _FunctionType):
            message = f"Module '{module_name}' has no method '{method_name}'"
            methods = _get_callable_methods(module)
            if methods:
                message += f"\n\nAvailable methods: {', '.join(methods)}"
            raise AttributeError(message)

        file = module.__file__
        absolute_path = Path(file)
        try:
            module_path = absolute_path.relative_to(_DOT_PATH.absolute())
        except ValueError:
            module_path = absolute_path
        print(
            f"\nRunning '{bright_blue}{module_path}{color}::"
            f"{bright_cyan}{method_name}{color}'..."
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
        func_nodes: list = [
            i for i in func_ast.body if isinstance(i, _FunctionDef) and i.name == method_name
        ]
        func_ast.body = func_nodes[-1:]

        # next, we insert some new logic into the beginning of the function. this imports
        # the sys module and assigns the current frame to a global var `__brownie_frame`
        injected_source = "import sys\nglobal __brownie_frame\n__brownie_frame = sys._getframe()"
        injected_ast = _parse(injected_source)
        func_ast.body[0].body = injected_ast.body + func_ast.body[0].body

        # now we compile the AST into a code object, using the module's `__dict__` as our globals
        # so that we have access to all the required imports and other objects
        f_locals: dict = module.__dict__.copy()
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


def _get_path(path_str: str) -> tuple[pathlib.Path, Project | None]:
    # Returns path to a python module
    path = Path(path_str).with_suffix(".py")

    if not get_loaded_projects():
        if not path.exists():
            raise FileNotFoundError(_cannot_find_message(path_str, _get_scripts_dirs()))
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
        raise FileNotFoundError(_cannot_find_message(path_str, _get_scripts_dirs()))

    if not path.exists():
        raise FileNotFoundError(
            _cannot_find_message(path_str, _get_scripts_dirs_for_path(path_str))
        )

    for project in get_loaded_projects():
        if path_str.startswith(project._path.as_posix()):
            return path.resolve(), project

    raise ProjectNotFound(f"{path_str} is not part of an active project")


def _get_callable_methods(module: ModuleType) -> list[str]:
    # Returns the names of public functions that may be called in a module.
    return sorted(
        name
        for name, func in vars(module).items()
        if isinstance(func, _FunctionType) and not name.startswith("_")
    )


def _get_script_methods(path: pathlib.Path) -> list[str]:
    # Returns the names of public top-level functions defined in a script,
    # without importing it. Unparsable scripts have no listed methods.
    # This is a static listing, not the runtime namespace: it tracks
    # straightforward rebinding and aliases, but cannot know what an imported
    # name refers to.
    try:
        with path.open() as fp:
            tree = _parse(fp.read())
    except (OSError, SyntaxError, ValueError):
        return []
    functions: set[str] = set()
    methods: dict[str, None] = {}
    for node in tree.body:
        if isinstance(node, (_FunctionDef, _AsyncFunctionDef)):
            functions.add(node.name)
            if not node.name.startswith("_"):
                methods[node.name] = None
        elif isinstance(node, _Assign):
            _track_assignments(methods, functions, node.targets, node.value)
        elif isinstance(node, _AnnAssign):
            if node.value is not None and isinstance(node.target, _Name):
                _track_assignments(methods, functions, [node.target], node.value)
        elif isinstance(node, _Delete):
            for target in node.targets:
                if isinstance(target, _Name):
                    methods.pop(target.id, None)
                    functions.discard(target.id)
    return list(methods)


def _track_assignments(
    methods: dict[str, None], functions: set[str], targets: list, value: Any
) -> None:
    # Updates the tracked methods for `target = value`: aliasing a known
    # function or a lambda adds a callable under every target, any other value
    # removes it. The right-hand side is classified once, before any target
    # is updated, so chained assignments and aliases after rebinding resolve
    # against the previous state. Targets are kept in `functions` too, even
    # private ones, so aliases of aliases resolve.
    if (isinstance(value, _Name) and value.id in functions) or isinstance(value, _Lambda):
        for target in targets:
            if isinstance(target, _Name):
                functions.add(target.id)
                if not target.id.startswith("_"):
                    methods[target.id] = None
    else:
        for target in targets:
            if isinstance(target, _Name):
                functions.discard(target.id)
                methods.pop(target.id, None)


def _get_scripts_tree(scripts_dir: pathlib.Path) -> str:
    # Returns a tree of the scripts and their callable methods within a directory.
    return "\n".join(_scripts_tree_lines(scripts_dir))


def _scripts_tree_lines(path: pathlib.Path, prefix: str = "") -> Iterator[str]:
    try:
        contents = sorted(path.iterdir(), key=lambda p: p.name)
    except OSError:
        return
    contents = [
        p
        for p in contents
        if not p.name.startswith((".", "_")) and (p.is_dir() or p.suffix == ".py")
    ]
    pointers = ["├── "] * (len(contents) - 1) + ["└── "]
    for pointer, child in zip(pointers, contents):
        extension = "│   " if pointer == "├── " else "    "
        if child.is_dir():
            yield f"{prefix}{pointer}{child.name}"
            yield from _scripts_tree_lines(child, prefix + extension)
        else:
            yield f"{prefix}{pointer}{child.stem}"
            methods = _get_script_methods(child)
            method_pointers = ["├── "] * (len(methods) - 1) + ["└── "]
            for method_pointer, method in zip(method_pointers, methods):
                yield f"{prefix}{extension}{method_pointer}{method}"


def _get_scripts_dirs() -> list[pathlib.Path]:
    # Returns the scripts directories searched when a script cannot be found:
    # every loaded project's scripts directory, or the scripts directory of
    # the project containing the working directory when no project is loaded.
    if get_loaded_projects():
        return [p._path.joinpath(p._structure["scripts"]) for p in get_loaded_projects()]
    project_path = check_for_project()
    if project_path is not None:
        return [project_path.joinpath(_load_project_structure_config(project_path)["scripts"])]
    return [Path("scripts")]


def _get_scripts_dirs_for_path(path_str: str) -> list[pathlib.Path]:
    # Returns the scripts directories relevant to an absolute script path:
    # the matching loaded project's scripts directory, or every searched
    # directory when the path belongs to no loaded project.
    for project in get_loaded_projects():
        if Path(path_str).is_relative_to(project._path):
            return [project._path.joinpath(project._structure["scripts"])]
    return _get_scripts_dirs()


def _display_path(path: pathlib.Path) -> str:
    # Returns a path relative to the working directory when possible.
    try:
        return path.relative_to(Path(".").absolute()).as_posix()
    except ValueError:
        return path.as_posix()


def _cannot_find_message(path_str: str, scripts_dirs: list[pathlib.Path]) -> str:
    message = f"Cannot find {path_str}"
    listings = []
    for scripts_dir in scripts_dirs:
        if scripts_dir.is_dir():
            tree = _get_scripts_tree(scripts_dir)
            if tree:
                listings.append(
                    f"Available scripts in path {_display_path(scripts_dir)}:\n\n{tree}"
                )
    if listings:
        message += "\n\n" + "\n\n".join(listings)
    return message


def _import_from_path(path: pathlib.Path) -> ModuleType:
    # Imports a module from the given path
    import_str = f"{'.'.join(path.parts[1:-1])}.{path.stem}"
    if import_str in _import_cache:
        _reload(_import_cache[import_str])
        return _import_cache[import_str]
    else:
        module = _import_module(import_str)
        _import_cache[import_str] = module
        return module


def _get_ast_hash(path: str | pathlib.Path) -> str:
    # Generates a hash based on the AST of a script.
    with Path(path).open() as fp:
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
                f"{Path(path).name}, unable to determine import spec for '{name}',"
                " the --update flag may not work correctly with this test file",
                ImportWarning,
            )
            continue
        if origin is not None and base_path in origin:
            with open(origin) as fp:
                ast_list.append(_parse(fp.read(), origin))

    dump = "\n".join(_dump(i) for i in ast_list)
    return sha1(dump.encode()).hexdigest()
