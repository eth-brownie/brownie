#!/usr/bin/python3

import json
from pathlib import Path
import shutil
import sys

from brownie.types import FalseyDict, StrictDict


IGNORE_MISSING = ['active_network', 'folders', 'logging']


def _load_config():
    path = Path(__file__).parent.joinpath("data/config.json")
    config = StrictDict(json.load(path.open()))
    config['folders'] = {
        'brownie': str(Path(__file__).parent),
        'project': None
    }
    # set logging
    try:
        config['logging'] = config['logging'][sys.argv[1]]
        config['logging'].setdefault('tx', 0)
        config['logging'].setdefault('exc', 0)
        for k, v in [(k, v) for k, v in config['logging'].items() if type(v) is list]:
            config['logging'][k] = v[1 if '--verbose' in sys.argv else 0]
    except:
        config['logging'] = {"tx": 1, "exc": 1}
    return config

def update_config():
    CONFIG._unlock()
    if CONFIG['folders']['project']:
        path = Path(CONFIG['folders']['project']).joinpath("brownie-config.json")
        if path.exists():
            _recursive_update(CONFIG, json.load(path.open()), [])
        else:
            shutil.copy(
                str(Path(CONFIG['folders']['brownie']).joinpath("data/config.json")),
                str(path)
            )
            print("WARNING: No config file found for this project. A new one has been created.")
    modify_network_config()

def modify_network_config(network = None):
    # modify network settings
    CONFIG._unlock()
    try:
        if not network:
            network = CONFIG['network_defaults']['name']
        CONFIG['active_network'] = CONFIG['networks'][network].copy()
        CONFIG['active_network']['name'] = network
        for key, value in CONFIG['network_defaults'].items():
            if key not in CONFIG['active_network']:
                CONFIG['active_network'][key] = value
        if 'persist' not in CONFIG['active_network']:
            CONFIG['active_network']['persist'] = False
    except KeyError:
        raise KeyError("Network '{}' is not defined in config.json".format(network))
    finally:
        CONFIG._lock()


# merges project .json with brownie .json
def _recursive_update(original, new, base):
    for k in new:
        if type(new[k]) is dict and k in original:
            _recursive_update(original[k], new[k], base+[k])
        else:
            original[k] = new[k]
    for k in [i for i in original if i not in new and not set(base+[i]).intersection(IGNORE_MISSING)]:
        print(
            "WARNING: Value '{}' not found in the config file for this project."
            " The default setting has been used.".format(".".join(base+[k]))
        )

# move argv flags into FalseyDict
ARGV = FalseyDict()
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
CONFIG = _load_config()
modify_network_config()