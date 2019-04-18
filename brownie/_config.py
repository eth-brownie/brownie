#!/usr/bin/python3

import json
from pathlib import Path
import sys

from brownie.types import FalseyDict, StrictDict



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

def update_config(network = None):
    CONFIG._unlock()
    if CONFIG['folders']['project']:
        path = Path(CONFIG['folders']['project']).joinpath("brownie-config.json")
        if path.exists():
            _recursive_update(CONFIG, json.load(path.open()))
    # modify network settings
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
    CONFIG._lock()


# merges project .json with brownie .json
def _recursive_update(original, new):
    for k in new:
        if type(new[k]) is dict and k in original:
            _recursive_update(original[k], new[k])
        else:
            original[k] = new[k]

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
update_config(CONFIG['network_defaults']['name'])