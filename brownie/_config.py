#!/usr/bin/python3

import json
from pathlib import Path
import shutil

from brownie.types.types import (
    FalseyDict,
    StrictDict,
    _Singleton
)

REPLACE = ['active_network', 'networks']
IGNORE = ['active_network', 'folders']


def _load_default_config():
    '''Loads the default configuration settings from brownie/data/config.json'''
    with Path(__file__).parent.joinpath("data/config.json").open() as fp:
        config = _Singleton("Config", (StrictDict,), {})(json.load(fp))
    config['folders'] = {
        'brownie': str(Path(__file__).parent),
        'project': None
    }
    config['active_network'] = {'name': None}
    return config


def load_project_config(project_path):
    '''Loads configuration settings from a project's brownie-config.json'''
    project_path = Path(project_path)
    if not project_path.exists():
        raise ValueError("Project does not exist!")
    CONFIG._unlock()
    CONFIG['folders']['project'] = str(project_path)
    config_path = project_path.joinpath("brownie-config.json")
    try:
        with config_path.open() as fp:
            _recursive_update(CONFIG, json.load(fp), [])
    except FileNotFoundError:
        shutil.copy(
            str(Path(CONFIG['folders']['brownie']).joinpath("data/config.json")),
            str(config_path)
        )
        print("WARNING: No config file found for this project. A new one has been created.")
    CONFIG.setdefault('active_network', {'name': None})
    CONFIG._lock()


def modify_network_config(network=None):
    '''Modifies the 'active_network' configuration settings'''
    CONFIG._unlock()
    try:
        if not network:
            network = CONFIG['network_defaults']['name']

        CONFIG['active_network'] = {
            **CONFIG['network_defaults'],
            **CONFIG['networks'][network]
        }
        CONFIG['active_network']['name'] = network

        if ARGV['cli'] == "test":
            CONFIG['active_network'].update(CONFIG['test'])
            if not CONFIG['active_network']['broadcast_reverting_tx']:
                print("WARNING: Reverting transactions will NOT be broadcasted.")
    except KeyError:
        raise KeyError(f"Network '{network}' is not defined in config.json")
    finally:
        CONFIG._lock()


# merges project .json with brownie .json
def _recursive_update(original, new, base):
    for k in new:
        if type(new[k]) is dict and k in REPLACE:
            original[k] = new[k]
        elif type(new[k]) is dict and k in original:
            _recursive_update(original[k], new[k], base+[k])
        else:
            original[k] = new[k]
    for k in [i for i in original if i not in new and not set(base+[i]).intersection(IGNORE)]:
        print(
            f"WARNING: '{'.'.join(base+[k])}' not found in the config file for this project."
            " The default setting has been used."
        )


# create argv object
ARGV = _Singleton("Argv", (FalseyDict,), {})()

# load config
CONFIG = _load_default_config()
