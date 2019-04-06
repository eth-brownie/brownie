#!/usr/bin/python3

import json
import os
import sys

from lib.services.datatypes import StrictDict, FalseyDict

# must happen in this order, color imports CONFIG
CONFIG = StrictDict()
from lib.services import color


def load_config(network=None):
    # set folders
    folder = sys.modules['__main__'].__file__
    folder = folder[:folder.rfind("/")]
    sys.path.insert(0, folder)
    CONFIG._unlock()
    CONFIG.clear()
    CONFIG.update(json.load(open(folder+"/config.json", 'r')))
    CONFIG['folders'] = {
        'brownie': folder,
        'project': os.path.abspath('.')
    }
    folders = os.path.abspath('.').split('/')
    for i in range(len(folders), 0, -1):
        folder = '/'.join(folders[:i])
        if os.path.exists(folder+'/brownie-config.json'):
            CONFIG['folders']['project'] = folder
            break
    sys.path.insert(1, ".")

    # update config
    if os.path.exists("brownie-config.json"):
        local_conf = json.load(open("brownie-config.json", 'r'))
        _recursive_update(CONFIG, local_conf)
    try:
        CONFIG['logging'] = CONFIG['logging'][sys.argv[1]]
        CONFIG['logging'].setdefault('tx', 0)
        CONFIG['logging'].setdefault('exc', 0)
        for k, v in [(k, v) for k, v in CONFIG['logging'].items() if type(v) is list]:
            CONFIG['logging'][k] = v[1 if '--verbose' in sys.argv else 0]
    except:
        CONFIG['logging'] = {"tx": 1, "exc": 1}

    # modify network settings
    if not network:
        network = CONFIG['network_defaults']['name']
    try:
        CONFIG['active_network'] = CONFIG['networks'][network]
        CONFIG['active_network']['name'] = network
        for key, value in CONFIG['network_defaults'].items():
            if key not in CONFIG['active_network']:
                CONFIG['active_network'][key] = value
        if 'persist' not in CONFIG['active_network']:
            CONFIG['active_network']['persist'] = False
    except KeyError:
        print(color.format_tb((
            sys.exc_info()[0],
            "Network '{}' is not defined in config.json".format(network),
            sys.exc_info()[2]
            )))
        sys.exit(1)
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
    ARGV['mode'] = "console" if sys.argv[1] == "console" else "script"

# load config
load_config(ARGV['network'])
