#!/usr/bin/python3

import json
import re
import shutil
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from hypothesis import settings as hp_settings
from hypothesis.database import DirectoryBasedExampleDatabase

from brownie._singleton import _Singleton

BROWNIE_FOLDER = Path(__file__).parent
DATA_FOLDER = Path.home().joinpath(".brownie")

DATA_SUBFOLDERS = ("accounts", "ethpm", "packages")

EVM_EQUIVALENTS = {"atlantis": "byzantium", "agharta": "petersburg"}


class ConfigContainer:
    def __init__(self):
        base_config = _load_config(BROWNIE_FOLDER.joinpath("data/default-config.yaml"))
        if Path.home().joinpath("brownie-config.yaml").exists():
            home_config = _load_config(Path.home().joinpath("brownie-config.yaml"))
            _recursive_update(base_config, home_config)

        network_config = _load_config(_get_data_folder().joinpath("network-config.yaml"))

        self.networks = {}
        for value in network_config["development"]:
            key = value["id"]
            if key in self.networks:
                raise ValueError(f"Multiple networks using ID '{key}'")
            self.networks[key] = value
        for value in [x for i in network_config["live"] for x in i["networks"]]:
            key = value["id"]
            if key in self.networks:
                raise ValueError(f"Multiple networks using ID '{key}'")
            self.networks[key] = value

        self.argv = defaultdict(lambda: None)
        self.settings = _Singleton("settings", (ConfigDict,), {})(base_config)
        self._active_network = None

        self.settings._lock()
        _modify_hypothesis_settings(self.settings["hypothesis"], "brownie-base", "default")

    def set_active_network(self, id_: str = None) -> Dict:
        """Modifies the 'active_network' configuration settings"""
        if id_ is None:
            id_ = self.settings["networks"]["default"]

        network = self.networks[id_].copy()
        key = "development" if "cmd" in network else "live"
        network["settings"] = self.settings["networks"][key].copy()

        self._active_network = network
        return network

    def clear_active(self):
        self._active_network = None

    @property
    def active_network(self):
        if self._active_network is None:
            raise ConnectionError("No active network")
        return self._active_network

    @property
    def network_type(self):
        if self._active_network is None:
            return None
        if "cmd" in self._active_network:
            return "development"
        else:
            return "live"

    @property
    def mode(self):
        return self.argv["cli"]


class ConfigDict(dict):
    """Dict subclass that prevents adding new keys when locked"""

    def __init__(self, values: Dict = {}) -> None:
        self._locked = False
        super().__init__()
        self.update(values)

    def __setitem__(self, key: str, value: Any) -> None:
        if self._locked and key not in self:
            raise KeyError(f"{key} is not a known config setting")
        if type(value) is dict:
            value = ConfigDict(value)
        super().__setitem__(key, value)

    def update(self, arg):  # type: ignore
        for k, v in arg.items():
            self.__setitem__(k, v)

    def _lock(self) -> None:
        """Locks the dict so that new keys cannot be added"""
        for v in [i for i in self.values() if type(i) is ConfigDict]:
            v._lock()
        self._locked = True

    def _unlock(self) -> None:
        """Unlocks the dict so that new keys can be added"""
        for v in [i for i in self.values() if type(i) is ConfigDict]:
            v._unlock()
        self._locked = False

    def _copy(self) -> Dict:
        config_copy = {}
        for key, value in self.items():
            if isinstance(value, ConfigDict):
                value = value._copy()
            config_copy[key] = value
        return config_copy


def _get_project_config_path(project_path: Path):
    if project_path.is_dir():
        path = project_path.joinpath("brownie-config")
    else:
        path = project_path
    suffix = next((i for i in (".yml", ".yaml", ".json") if path.with_suffix(i).exists()), None)
    if suffix is not None:
        return path.with_suffix(suffix)
    return None


def _load_config(project_path: Path) -> Dict:
    # Loads configuration data from a file, returns as a dict
    path = _get_project_config_path(project_path)
    if path is None:
        return {}

    with path.open() as fp:
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(fp)
        raw_json = fp.read()
    valid_json = re.sub(r'\/\/[^"]*?(?=\n|$)', "", raw_json)
    return json.loads(valid_json)


def _load_project_config(project_path: Path) -> None:
    # Loads configuration settings from a project's brownie-config.yaml
    config_path = project_path.joinpath("brownie-config")
    config_data = _load_config(config_path)
    if not config_data:
        return

    if "network" in config_data:
        warnings.warn(
            "The `network` field in `brownie-config.yaml` has been deprecated. "
            "Network settings are now handled via `brownie network` in the CLI. "
            f"Remove `network` from {config_path} to silence this warning.",
            DeprecationWarning,
        )
        del config_data["network"]

    CONFIG.settings._unlock()
    _recursive_update(CONFIG.settings, config_data)
    CONFIG.settings._lock()
    if "hypothesis" in config_data:
        _modify_hypothesis_settings(config_data["hypothesis"], "brownie", "brownie-base")


def _load_project_compiler_config(project_path: Optional[Path]) -> Dict:
    if not project_path:
        return CONFIG.settings["compiler"]

    compiler_data = CONFIG.settings["compiler"]._copy()
    project_data = _load_config(project_path.joinpath("brownie-config")).get("compiler", {})
    _recursive_update(compiler_data, project_data)

    return compiler_data


def _load_project_dependencies(project_path: Path) -> List:
    data = _load_config(project_path.joinpath("brownie-config"))
    dependencies = data.get("dependencies", []) or []
    if isinstance(dependencies, str):
        dependencies = [dependencies]
    return dependencies


def _modify_hypothesis_settings(settings, name, parent):
    hp_settings.register_profile(
        name,
        parent=hp_settings.get_profile(parent),
        database=DirectoryBasedExampleDatabase(_get_data_folder().joinpath("hypothesis")),
        **settings,
    )
    hp_settings.load_profile(name)


def _recursive_update(original: Dict, new: Dict) -> None:
    # merges project config with brownie default config
    for k in new:
        if k in original and isinstance(new[k], dict):
            _recursive_update(original[k], new[k])
        else:
            original[k] = new[k]


def _update_argv_from_docopt(args: Dict) -> None:
    CONFIG.argv.update(dict((k.lstrip("-"), v) for k, v in args.items()))


def _get_data_folder() -> Path:
    return DATA_FOLDER


def _make_data_folders(data_folder: Path) -> None:
    # create data folder structure
    data_folder.mkdir(exist_ok=True)
    for folder in DATA_SUBFOLDERS:
        data_folder.joinpath(folder).mkdir(exist_ok=True)

    if not data_folder.joinpath("network-config.yaml").exists():
        shutil.copyfile(
            BROWNIE_FOLDER.joinpath("data/network-config.yaml"),
            data_folder.joinpath("network-config.yaml"),
        )


warnings.filterwarnings("once", category=DeprecationWarning, module="brownie")

# create data folders
_make_data_folders(DATA_FOLDER)

CONFIG = _Singleton("Config", (ConfigContainer,), {})()
