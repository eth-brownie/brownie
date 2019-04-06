#!/usr/bin/python3


from pathlib import Path
import shutil

import brownie.config as config


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
    config.CONFIG['folders']['project'] = path
    return path


def load_project(path=None):
    if path is None:
        path = _check_for_project('.')
    if not path or not Path(path).joinpath("brownie-config.json").exists():
        raise SystemError("Could not find brownie project")
    config.CONFIG['folders']['project'] = str(Path(path).resolve())
    _create_build_folders(path)