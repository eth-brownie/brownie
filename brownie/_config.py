#!/usr/bin/python3

import json
from pathlib import Path
import shutil
import sys

from brownie.types.types import (
    FalseyDict,
    StrictDict,
    _Singleton
)

REPLACE = ['active_network', 'networks']
IGNORE = ['active_network', 'folders', 'logging']


def _load_default_config():
    '''Loads the default configuration settings from brownie/data/config.json'''
    path = Path(__file__).parent.joinpath("data/config.json")
    config = _Singleton("Config", (StrictDict,), {})(json.load(path.open()))
    config['folders'] = {
        'brownie': str(Path(__file__).parent),
        'project': None
    }
    config['active_network'] = {'name': None}
    # set logging
    try:
        config['logging'] = config['logging'][sys.argv[1]]
        config['logging'].setdefault('tx', 0)
        config['logging'].setdefault('exc', 0)
        for k, v in [(k, v) for k, v in config['logging'].items() if type(v) is list]:
            config['logging'][k] = v[1 if '--verbose' in sys.argv else 0]
    except Exception:
        config['logging'] = {"tx": 1, "exc": 1}
    return config


def load_project_config(project_path):
    '''Loads configuration settings from a project's brownie-config.json'''
    project_path = Path(project_path)
    if not project_path.exists():
        raise ValueError("Project does not exist!")
    CONFIG._unlock()
    CONFIG['folders']['project'] = str(project_path)
    config_path = project_path.joinpath("brownie-config.json")
    if config_path.exists():
        _recursive_update(CONFIG, json.load(config_path.open()), [])
    else:
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

        CONFIG['active_network'] = {**CONFIG['network_defaults'], **CONFIG['networks'][network]}
        CONFIG['active_network']['name'] = network

        if ARGV['cli'] == "test":
            CONFIG['active_network'].update(CONFIG['test'])
            if not CONFIG['active_network']['broadcast_reverting_tx']:
                print("WARNING: Reverting transactions will NOT be broadcasted.")
    except KeyError:
        raise KeyError("Network '{}' is not defined in config.json".format(network))
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
            "WARNING: Value '{}' not found in the config file for this project."
            " The default setting has been used.".format(".".join(base+[k]))
        )


# move argv flags into FalseyDict
ARGV = _Singleton("Argv", (FalseyDict,), {})()
for key in [i for i in sys.argv if i[:2] == "--"]:
    idx = sys.argv.index(key)
    if len(sys.argv) >= idx+2 and sys.argv[idx+1][:2] != "--":
        ARGV[key[2:]] = sys.argv[idx+1]
    else:
        ARGV[key[2:]] = True

# used to determine various behaviours in other modules
if len(sys.argv) > 1:
    ARGV['cli'] = sys.argv[1]

# load config
CONFIG = _load_default_config()
