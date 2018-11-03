#!/usr/bin/python3

import json
import os
import sys


if "--help" in sys.argv:
    sys.exit("""Usage: brownie init

This command creates the default structure for the brownie environment:

/contracts            Solidity contracts
/deployments          Python scripts relating to contract deployment
/tests                Python scripts for unit testing
brownie-config.json   Overrides default brownie settings""")


if sys.modules['__main__'].__file__.rsplit('/',maxsplit = 1)[0] in os.path.abspath('.'):
    sys.exit("""ERROR: You cannot init the main brownie installation folder.
Create a new folder for your project and run brownie init there.""")


if '--force' not in sys.argv and (
    os.path.exists('../brownie-config.json') or
    os.path.exists('../../brownie.config.json')
    ):
    sys.exit("ERROR: Cannot init a brownie subfolder. Use --force to override.")

FOLDERS = [
    'contracts',
    'deployments',
    'tests'
]
FILES = [
    ('deployments/__init__.py',''),
    ('tests/__init__.py',''),
    ('brownie-config.json','{\n\n}')
]

init = False
for folder in [i for i in FOLDERS if not os.path.exists(i)]:
    init = True
    os.mkdir(folder)

for filename, content in [i for i in FILES if not os.path.exists(i[0])]:
    init = True
    open(filename,'a').write(content)

if init:
    sys.exit("Brownie environment has been initiated for {}".format(os.path.abspath('.')))
sys.exit("ERROR: Brownie was already initiated in this folder.")