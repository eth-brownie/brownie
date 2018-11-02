#!/usr/bin/python3

import json
import os
import sys

CONFIG = json.load(open(sys.modules['__main__'].__file__.rsplit('/',maxsplit = 1)[0]+'/config.json', 'r'))

conf_path = os.path.abspath('.')+"/tests/config.json"
if os.path.exists(conf_path):
    for k,v in json.load(open(conf_path, 'r')).items():
        if type(v) is dict and k in CONFIG:
            CONFIG[k].update(v)
        else: CONFIG[k] = v