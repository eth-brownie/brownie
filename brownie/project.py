#!/usr/bin/python3


from pathlib import Path
import shutil
import sys

from brownie.network.contract import ContractContainer
from brownie.utils.compiler import compile_contracts
import brownie.config


__all__ = ['project', '__project']

__project = True
project = sys.modules[__name__]

CONFIG = brownie.config.CONFIG

FOLDERS = ["contracts", "scripts", "tests"]
BUILD_FOLDERS = ["build", "build/contracts", "build/networks"]


def check_for_project(path):
    path = Path(path).resolve()
    for folder in [path]+list(path.parents):
        if folder.joinpath("brownie-config.json").exists():
            return folder
    return None


def _create_build_folders(path):
    path = Path(path).resolve()
    for folder in [i for i in BUILD_FOLDERS]:
        path.joinpath(folder).mkdir(exist_ok=True)


def new(path=".", ignore_subfolder=False):
    if CONFIG['folders']['project']:
        raise SystemError("Project has already been loaded")
    path = Path(path)
    path.mkdir(exist_ok=True)
    path = path.resolve()
    if not ignore_subfolder:
        check = check_for_project(path)
        if check and check != path:
            raise SystemError("Cannot make a new project inside the subfolder of an existing project.")
    for folder in [i for i in FOLDERS]:
        path.joinpath(folder).mkdir(exist_ok=True)
    if not path.joinpath('brownie-config.json').exists():
        shutil.copy(
            str(Path(CONFIG['folders']['brownie']).joinpath("data/config.json")),
            str(path.joinpath('brownie-config.json'))
        )
    _create_build_folders(path)
    CONFIG['folders']['project'] = str(path)
    sys.path.insert(0, str(path))
    return str(path)


def load(path=None):
    if CONFIG['folders']['project']:
        raise SystemError("Project has already been loaded")
    if path is None:
        path = check_for_project('.')
    if not path or not Path(path).joinpath("brownie-config.json").exists():
        raise SystemError("Could not find brownie project")
    path = Path(path).resolve()
    CONFIG['folders']['project'] = str(path)
    sys.path.insert(0, str(path))
    brownie.config.update_config()
    _create_build_folders(path)
    for name, build in compile_contracts(path.joinpath('contracts')).items():
        if build['type'] == "interface":
            continue
        container = ContractContainer(build)
        globals()[name] = container
        __all__.append(name)
        # if running via CLI, ensure container is available via main brownie package
        if hasattr(sys.modules['__main__'], '__brownie_cli'):
            sys.modules['brownie'].__dict__[name] = container
            sys.modules['brownie'].__all__.append(name)
        # if running via interpreter, add to main namespace if package was imported via from
        elif '__project' in sys.modules['__main__'].__dict__:
            sys.modules['__main__'].__dict__[name] = container
