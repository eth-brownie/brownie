#!/usr/bin/python3

import json
import os
import sys

if not os.path.exists('tests'):
    os.mkdir('tests')
    open('tests/__init__.py','a')

if not os.path.exists('brownie-config.json'):
    open('brownie-config.json','a').write("{\n\n}")

sys.exit("Brownie has been initiated for {}".format(os.path.abspath('.')))