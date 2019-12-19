#!/usr/bin/python3

import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from brownie._singleton import _Singleton

BROWNIE_FOLDER = Path(__file__).parent
DATA_FOLDER = Path.home().joinpath(".brownie")

REPLACE = ["active_network", "networks"]


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
        raise ValueError("Project does not exist!")
    with path.open() as fp:
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(fp)
        raw_json = fp.read()
    valid_json = re.sub(r'\/\/[^"]*?(?=\n|$)', "", raw_json)
    return json.loads(valid_json)


def _load_default_config() -> "ConfigDict":
    # Loads the default configuration settings from brownie/data/config.yaml
    base_config = BROWNIE_FOLDER.joinpath("data/config.yaml")
    default_config = DATA_FOLDER.joinpath("brownie-config.yaml")

    if not DATA_FOLDER.exists():
        DATA_FOLDER.mkdir()
    if not default_config.exists():
        shutil.copy(base_config, default_config)

    config = _Singleton("Config", (ConfigDict,), {})(_load_config(base_config))  # type: ignore
    _recursive_update(config, _load_config(default_config), [])
    config["active_network"] = {"name": None}
    return config


def _load_project_config(project_path: Path) -> None:
    # Loads configuration settings from a project's brownie-config.yaml
    config_data = _load_config(project_path.joinpath("brownie-config"))
    CONFIG._unlock()
    _recursive_update(CONFIG, config_data, [])
    CONFIG.setdefault("active_network", {"name": None})
    CONFIG._lock()


def _load_project_compiler_config(project_path: Optional[Path], compiler: str) -> Dict:
    if not project_path:
        return CONFIG["compiler"][compiler]
    config_data = _load_config(project_path.joinpath("brownie-config"))
    return config_data["compiler"][compiler]


def _modify_network_config(network: str = None) -> Dict:
    """Modifies the 'active_network' configuration settings"""
    CONFIG._unlock()
    try:
        if not network:
            network = CONFIG["network"]["default"]

        CONFIG["active_network"] = {
            **CONFIG["network"]["settings"],
            **CONFIG["network"]["networks"][network],
        }
        CONFIG["active_network"]["name"] = network

        if ARGV["cli"] == "test":
            CONFIG["active_network"].update(CONFIG["pytest"])
            if not CONFIG["active_network"]["reverting_tx_gas_limit"]:
                print("WARNING: Reverting transactions will NOT be broadcasted.")
        return CONFIG["active_network"]
    except KeyError:
        raise KeyError(f"Network '{network}' is not defined in config.json")
    finally:
        CONFIG._lock()


def _recursive_update(original: Dict, new: Dict, base: List) -> None:
    # merges project config with brownie default config
    for k in new:
        if type(new[k]) is dict and k in REPLACE:
            original[k] = new[k]
        elif type(new[k]) is dict and k in original:
            _recursive_update(original[k], new[k], base + [k])
        else:
            original[k] = new[k]


def _update_argv_from_docopt(args: Dict) -> None:
    ARGV.update(dict((k.lstrip("-"), v) for k, v in args.items()))


# create argv object
ARGV = _Singleton("Argv", (defaultdict,), {})(lambda: None)  # type: ignore

# load config
CONFIG = _load_default_config()
