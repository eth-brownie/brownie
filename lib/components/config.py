#!/usr/bin/python3

import json
import os
import sys


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

if os.path.exists("brownie-config.json"):
    for k,v in json.load(open("brownie-config.json", 'r')).items():
        if type(v) is dict and k in CONFIG:
            CONFIG[k].update(v)
        else: CONFIG[k] = v

try:
    CONFIG['logging'] = CONFIG['logging'][sys.argv[1]]
    for k,v in [(k,v) for k,v in CONFIG['logging'].items() if type(v) is list]:
       CONFIG['logging'][k] = v[1 if '--verbose' in sys.argv else 0]
except:
    CONFIG['logging'] = {"tx":1 ,"exc":1}

if '--network' in sys.argv:
    set_network(sys.argv[sys.argv.index('--network')+1])
else:
    set_network(CONFIG['network_defaults']['name'])