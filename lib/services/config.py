#!/usr/bin/python3

import json
import os
import sys


# modifies config network settings
def set_network(name):
    try:
        CONFIG['active_network'] = CONFIG['networks'][name]
        CONFIG['active_network']['name'] = name
        for key,value in CONFIG['network_defaults'].items():
            if key not in CONFIG['active_network']:
                CONFIG['active_network'][key] = value
        if 'persist' not in CONFIG['active_network']:
            CONFIG['active_network']['persist'] = False
    except KeyError:
        raise KeyError("Network '{}' is not defined in config.json".format(name))


# merges project .json with brownie .json 
def _recursive_update(original, new):
    for k in new:
        if type(new[k]) is dict and k in original:
            _recursive_update(original[k], new[k])
        else: original[k] = new[k]


# dictionary that returns False if key does not exist
class FalseyDict:

    def __init__(self):
        self._dict = {}

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __getitem__(self, key):
        if key in self._dict:
            return self._dict[key]
        return False


# move argv options into FalseyDict
ARGV = FalseyDict()
for key in [i for i in sys.argv if i[:2]=="--"]:
    idx = sys.argv.index(key)
    if len(sys.argv) >= idx+2 and sys.argv[idx+1][:2] != "--":
        ARGV[key] = sys.argv[idx+1]
    else:
        ARGV[key] = True
ARGV['mode'] = "console" if sys.argv[1] == "console" else "script"


# set folders
folder = sys.modules['__main__'].__file__
folder = folder[:folder.rfind("/")]
sys.path.insert(0, folder)
CONFIG = json.load(open(folder+"/config.json", 'r'))
CONFIG['folders'] = {
    'brownie': folder,
    'project': os.path.abspath('.')
}
folders = os.path.abspath('.').split('/')
for i in range(len(folders),0,-1):
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
    CONFIG['logging'].setdefault('tx',0)
    CONFIG['logging'].setdefault('exc',0)
    for k,v in [(k,v) for k,v in CONFIG['logging'].items() if type(v) is list]:
       CONFIG['logging'][k] = v[1 if '--verbose' in sys.argv else 0]
except:
    CONFIG['logging'] = {"tx":1 ,"exc":1}


# set network
if ARGV['network']:
    set_network(ARGV['network'])
else:
    set_network(CONFIG['network_defaults']['name'])