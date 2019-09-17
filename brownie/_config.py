#!/usr/bin/python3

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Optional

from brownie._singleton import _Singleton

REPLACE = ["active_network", "networks"]
IGNORE = ["active_network", "brownie_folder"]


class ConfigDict(dict):
    """Dict subclass that prevents adding new keys when locked"""

    def __init__(self, values: Dict = {}) -> None:
        self._locked = False
        super().__init__()
        self.update(values)

    def __setitem__(self, key: Any, value: Any) -> None:
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


def _load_json(path: "Path") -> Any:
    with path.open() as fp:
        raw_json = fp.read()
    valid_json = re.sub(r'\/\/[^"]*?(?=\n|$)', "", raw_json)
    return json.loads(valid_json)


def _load_default_config() -> Any:
    """Loads the default configuration settings from brownie/data/config.json"""
    brownie_path = Path(__file__).parent
    path = brownie_path.joinpath("data/config.json")
    config = _Singleton("Config", (ConfigDict,), {})(_load_json(path))
    config.update({"active_network": {"name": None}, "brownie_folder": brownie_path})
    return config


def _get_project_config_file(project_path: "Path") -> Any:
    project_path = Path(project_path)
    if not project_path.exists():
        raise ValueError("Project does not exist!")
    config_path: "Path" = Path(project_path).joinpath("brownie-config.json")
    return _load_json(config_path)


def _load_project_config(project_path: "Path") -> None:
    """Loads configuration settings from a project's brownie-config.json"""
    config_data = _get_project_config_file(project_path)
    CONFIG._unlock()
    _recursive_update(CONFIG, config_data, [])
    CONFIG.setdefault("active_network", {"name": None})
    CONFIG._lock()


def _load_project_compiler_config(project_path: Optional["Path"], compiler: Any) -> Any:
    if not project_path:
        return CONFIG["compiler"][compiler]
    config_data = _get_project_config_file(project_path)
    return config_data["compiler"][compiler]


def _modify_network_config(network: str = None) -> Any:
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


# merges project .json with brownie .json
def _recursive_update(original: Any, new: Any, base: Any) -> None:
    for k in new:
        if type(new[k]) is dict and k in REPLACE:
            original[k] = new[k]
        elif type(new[k]) is dict and k in original:
            _recursive_update(original[k], new[k], base + [k])
        else:
            original[k] = new[k]
    for k in [
        i for i in original if i not in new and not set(base + [i]).intersection(IGNORE)
    ]:
        print(
            f"WARNING: '{'.'.join(base+[k])}' not found in the config file for this project."
            " The default setting has been used."
        )


def _update_argv_from_docopt(args: Any) -> None:
    ARGV.update(dict((k.lstrip("-"), v) for k, v in args.items()))


# create argv object
ARGV = _Singleton("Argv", (defaultdict,), {})(lambda: None)  # type: ignore

# load config
CONFIG = _load_default_config()
