#!/usr/bin/python3


from pathlib import Path
import shutil
import sys

from brownie.network.contract import ContractContainer
from brownie.utils.compiler import compile_contracts
import brownie.config


__all__ = ['new_project', 'load_project']

CONFIG = brownie.config.CONFIG

FOLDERS = ["contracts", "scripts", "tests"]
BUILD_FOLDERS = ["build", "build/contracts", "build/networks"]


def _check_for_project(path):
    path = Path(path).resolve()
    for folder in [path]+list(path.parents):
        if folder.joinpath("brownie-config.json").exists():
            return folder
    return None


def _create_build_folders(path):
    path = Path(path).resolve()
    for folder in [i for i in BUILD_FOLDERS]:
        path.joinpath(folder).mkdir(exist_ok=True)


def new_project(path=".", ignore_subfolder=False):
    path = Path(path)
    path.mkdir(exist_ok=True)
    path = path.resolve()
    if not ignore_subfolder:
        check = _check_for_project(path)
        if check and check != path:
            raise SystemError("Cannot make a new project inside the subfolder of an existing project.")
    
    for folder in [i for i in FOLDERS]:
        path.joinpath(folder).mkdir(exist_ok=True)
    if not path.joinpath('brownie-config.json').exists():
        shutil.copy(
            str(Path(__file__).parents[1].joinpath("config.json")),
            str(path.joinpath('brownie-config.json'))
        )
    _create_build_folders(path)
    CONFIG['folders']['project'] = path
    return path


def load_project(path=None):
    if path is None:
        path = _check_for_project('.')
    if not path or not Path(path).joinpath("brownie-config.json").exists():
        raise SystemError("Could not find brownie project")
    path = Path(path).resolve()
    CONFIG['folders']['project'] = str(path)
    brownie.config.update_config()
    _create_build_folders(path)
    for name, build in compile_contracts(path.joinpath('contracts')).items():
        if build['type'] == "interface":
            continue
        #if name in self._network_dict:
        #    raise AttributeError("Namespace collision between Contract '{0}' and 'Network.{0}'".format(name))
        #self._network_dict[name] = contract.ContractContainer(build, self._network_dict)
        container = ContractContainer(build)
        globals()[name] = container
        if set(__all__).issubset(sys.modules['__main__'].__dict__):
            sys.modules['__main__'].__dict__[name] = container