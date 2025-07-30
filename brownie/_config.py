#!/usr/bin/python3
import json
import os
import pathlib
import shutil
import sys
import warnings
from importlib import resources
from typing import Any, DefaultDict, Dict, Final, List, Literal, NewType, Optional, final

import yaml
from dotenv import dotenv_values, load_dotenv
from hypothesis import Phase
from hypothesis import settings as hp_settings
from hypothesis.database import DirectoryBasedExampleDatabase

from brownie._c_constants import Path, deepcopy, defaultdict, json_loads, regex_sub
from brownie._expansion import expand_posix_vars
from brownie._singleton import _Singleton

__version__: Final = "1.22.0"

BROWNIE_FOLDER: Final = Path(sys.modules["brownie"].__file__)  # type: ignore [arg-type]
DATA_FOLDER: Final = Path.home().joinpath(".brownie")

DATA_SUBFOLDERS: Final = "accounts", "packages"

EVM_EQUIVALENTS: Final = {"atlantis": "byzantium", "agharta": "petersburg"}

python_version: Final = (
    f"{sys.version_info.major}.{sys.version_info.minor}"
    f".{sys.version_info.micro} {sys.version_info.releaselevel}"
)
REQUEST_HEADERS: Final = {"User-Agent": f"Brownie/{__version__} (Python/{python_version})"}


NetworkType = Literal["live", "development", None]
NetworkConfig = NewType("NetworkConfig", Dict[str, Any])
# TODO: Make this a typed dict


@final
class ConfigContainer:
    def __init__(self) -> None:
        base_config = _load_config(BROWNIE_FOLDER.joinpath("data/default-config.yaml"))
        if Path.home().joinpath("brownie-config.yaml").exists():
            home_config = _load_config(Path.home().joinpath("brownie-config.yaml"))
            _recursive_update(base_config, home_config)

        networks: Dict[str, dict] = {}
        self.networks: Final = networks

        network_config = _load_config(_get_data_folder().joinpath("network-config.yaml"))
        for value in network_config["development"]:
            key = value["id"]
            if key in networks:
                raise ValueError(f"Multiple networks using ID '{key}'")
            networks[key] = value
        for value in [x for i in network_config["live"] for x in i["networks"]]:
            key = value["id"]
            if key in networks:
                raise ValueError(f"Multiple networks using ID '{key}'")
            networks[key] = value

        # make sure chainids are always strings
        for settings in networks.values():
            if "chainid" in settings:
                settings["chainid"] = str(settings["chainid"])

        self.argv: Final[DefaultDict[str, Any]] = defaultdict(_None_factory)
        self.settings: Final["ConfigDict"] = _Singleton("settings", (ConfigDict,), {})(base_config)
        self._active_network: Optional[NetworkConfig] = None

        self.settings._lock()
        _modify_hypothesis_settings(self.settings["hypothesis"], "brownie-base", "default")

    def set_active_network(self, id_: Optional[str] = None) -> NetworkConfig:
        """Modifies the 'active_network' configuration settings"""
        if id_ is None:
            id_ = self.settings["networks"]["default"]

        network = NetworkConfig(deepcopy(self.networks[id_]))  # type: ignore [index]
        key = "development" if "cmd" in network else "live"
        network["settings"] = self.settings["networks"][key].copy()

        if (
            key == "development"
            and isinstance(cmd_settings := network["cmd_settings"], dict)
            and "fork" in cmd_settings
        ):

            fork = cmd_settings["fork"]
            if fork in self.networks:
                fork_settings: dict = self.networks[fork]
                cmd_settings["fork"] = fork_settings["host"]
                network["chainid"] = fork_settings["chainid"]
                if "chain_id" not in cmd_settings:
                    cmd_settings["chain_id"] = int(fork_settings["chainid"])
                if "explorer" in fork_settings:
                    network["explorer"] = fork_settings["explorer"]

            cmd_settings["fork"] = os.path.expandvars(cmd_settings["fork"])

        self._active_network = network
        return network

    def clear_active(self) -> None:
        self._active_network = None

    @property
    def active_network(self) -> NetworkConfig:
        if self._active_network is None:
            raise ConnectionError("No active network")
        return self._active_network

    @property
    def network_type(self) -> NetworkType:
        if self._active_network is None:
            return None
        return "development" if "cmd" in self._active_network else "live"

    @property
    def mode(self) -> Optional[str]:
        return self.argv["cli"]


@final
class ConfigDict(Dict[str, Any]):
    """Dict subclass that prevents adding new keys when locked"""

    def __init__(self, values: Dict[str, Any] = {}) -> None:
        self._locked = False
        super().__init__()
        self.update(values)

    def __setitem__(self, key: str, value: Any) -> None:
        if self._locked and key not in self:
            raise KeyError(f"{key} is not a known config setting")
        if type(value) is dict:
            value = ConfigDict(value)
        super().__setitem__(key, value)

    def update(self, arg: Dict[str, Any]) -> None:  # type: ignore [override]
        for k, v in arg.items():
            self.__setitem__(k, v)

    def _lock(self) -> None:
        """Locks the dict so that new keys cannot be added"""
        for obj in self.values():
            if type(obj) is ConfigDict:
                obj._lock()
        self._locked = True

    def _unlock(self) -> None:
        """Unlocks the dict so that new keys can be added"""
        for obj in self.values():
            if type(obj) is ConfigDict:
                obj._unlock()
        self._locked = False

    def _copy(self) -> Dict[str, Any]:
        config_copy = {}
        for key, value in self.items():
            if isinstance(value, ConfigDict):
                value = value._copy()
            config_copy[key] = value
        return config_copy


def _get_project_config_path(project_path: pathlib.Path) -> Optional[pathlib.Path]:
    if project_path.is_dir():
        path = project_path.joinpath("brownie-config")
    else:
        path = project_path
    suffix = next((i for i in (".yml", ".yaml", ".json") if path.with_suffix(i).exists()), None)
    return None if suffix is None else path.with_suffix(suffix)


def _load_config(project_path: pathlib.Path) -> Dict:
    """Loads configuration data from a file, returns as a dict"""
    path = _get_project_config_path(project_path)
    if path is None:
        return {}

    with path.open() as fp:
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(fp) or {}
        raw_json = fp.read()
    valid_json = regex_sub(r'\/\/[^"]*?(?=\n|$)', "", raw_json)
    return json_loads(valid_json)


def _load_project_config(project_path: pathlib.Path) -> None:
    """Loads configuration settings from a project's brownie-config.yaml"""
    config_path = project_path.joinpath("brownie-config")
    config_data = _load_config(config_path)
    config_vars = _load_project_envvars(project_path)

    if "dotenv" in config_data:
        if not isinstance(config_data["dotenv"], str):
            raise ValueError(f'Invalid value passed to dotenv: {config_data["dotenv"]}')
        env_path = project_path.joinpath(config_data["dotenv"])
        if not env_path.is_file():
            raise ValueError(f"Dotenv specified in config but not found at path: {env_path}")
        config_vars.update(dotenv_values(dotenv_path=env_path))  # type: ignore
        load_dotenv(dotenv_path=env_path)
        config_data = expand_posix_vars(config_data, config_vars)

    if not config_data:
        return

    if "network" in config_data:
        warnings.warn(
            "The `network` field in `brownie-config.yaml` has been deprecated. "
            "Network settings are now handled via `brownie networks` in the CLI. "
            f"Remove `network` from {config_path} to silence this warning.",
            DeprecationWarning,
        )
        del config_data["network"]

    # Update the network config cmd_settings with project specific cmd_settings
    if "networks" in config_data and isinstance(config_data["networks"], dict):
        for network, values in config_data["networks"].items():
            if (
                network != "default"
                and network in CONFIG.networks.keys()
                and "cmd_settings" in values
                and isinstance(values["cmd_settings"], dict)
            ):
                if "cmd_settings" in CONFIG.networks[network]:
                    _recursive_update(
                        CONFIG.networks[network]["cmd_settings"], values["cmd_settings"]
                    )
                else:
                    CONFIG.networks[network]["cmd_settings"] = values["cmd_settings"]

    settings = CONFIG.settings
    settings._unlock()
    _recursive_update(settings, config_data)
    _recursive_update(settings, expand_posix_vars(settings, config_vars))

    settings._lock()
    if "hypothesis" in config_data:
        _modify_hypothesis_settings(config_data["hypothesis"], "brownie", "brownie-base")


def _load_project_compiler_config(project_path: Optional[pathlib.Path]) -> Dict:
    if not project_path:
        return CONFIG.settings["compiler"]

    compiler_data = CONFIG.settings["compiler"]._copy()
    project_data = _load_config(project_path.joinpath("brownie-config")).get("compiler", {})
    _recursive_update(compiler_data, project_data)

    return compiler_data


def _load_project_envvars(project_path: pathlib.Path) -> Dict:
    config_vars = dict(os.environ)
    settings = CONFIG.settings
    if settings.get("dotenv"):
        dotenv_path = settings["dotenv"]
        if not isinstance(dotenv_path, str):
            raise ValueError(f"Invalid value passed to dotenv: {dotenv_path}")
        env_path = project_path.joinpath(dotenv_path)
        if not env_path.is_file():
            raise ValueError(f"Dotenv specified in config but not found at path: {env_path}")
        config_vars.update(dotenv_values(dotenv_path=env_path))  # type: ignore
    return config_vars


def _load_project_structure_config(project_path):
    structure = CONFIG.settings["project_structure"]._copy()

    path = _get_project_config_path(project_path)
    if path is None:
        return structure

    data = _load_config(project_path).get("project_structure", {})
    structure.update(data)
    return structure


def _load_project_dependencies(project_path: pathlib.Path) -> List[str]:
    data = _load_config(project_path.joinpath("brownie-config"))
    dependencies = data.get("dependencies", []) or []
    if isinstance(dependencies, str):
        dependencies = [dependencies]
    return dependencies


def _modify_hypothesis_settings(settings, name, parent=None):
    settings = settings.copy()
    if parent is None:
        parent = hp_settings._current_profile  # type: ignore [attr-defined]

    if "phases" in settings:
        try:
            settings["phases"] = [getattr(Phase, k) for k, v in settings["phases"].items() if v]
        except AttributeError as exc:
            raise ValueError(f"'{exc.args[0]}' is not a valid hypothesis phase setting")

    hp_settings.register_profile(
        name,
        parent=hp_settings.get_profile(parent),
        database=DirectoryBasedExampleDatabase(_get_data_folder().joinpath("hypothesis")),  # type: ignore [arg-type]
        **settings,
    )
    hp_settings.load_profile(name)


def _recursive_update(original: Dict, new: Dict) -> None:
    """Recursively merges a new dict into the original dict"""
    if not original:
        original = {}
    for k in new:
        if k in original and isinstance(new[k], dict):
            _recursive_update(original[k], new[k])
        else:
            original[k] = new[k]


def _update_argv_from_docopt(args: Dict[str, Any]) -> None:
    CONFIG.argv.update({k.lstrip("-"): v for k, v in args.items()})


def _get_data_folder() -> pathlib.Path:
    return DATA_FOLDER


def _make_data_folders(data_folder: pathlib.Path) -> None:
    # create data folder structure
    data_folder.mkdir(exist_ok=True)
    for folder in DATA_SUBFOLDERS:
        data_folder.joinpath(folder).mkdir(exist_ok=True)

    if not data_folder.joinpath("network-config.yaml").exists():
        shutil.copyfile(
            BROWNIE_FOLDER.joinpath("data/network-config.yaml"),
            data_folder.joinpath("network-config.yaml"),
        )

    if not data_folder.joinpath("providers-config.yaml").exists():
        shutil.copyfile(
            BROWNIE_FOLDER.joinpath("data/providers-config.yaml"),
            data_folder.joinpath("providers-config.yaml"),
        )


def _None_factory() -> None:
    return None

warnings.filterwarnings("once", category=DeprecationWarning, module="brownie")

# create data folders
_make_data_folders(DATA_FOLDER)

CONFIG: Final[ConfigContainer] = _Singleton("Config", (ConfigContainer,), {})()
