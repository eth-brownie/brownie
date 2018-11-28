#!/usr/bin/python3

import os
import sys

BROWNIE_FOLDER = sys.modules['__main__'].__file__.rsplit('/', maxsplit = 1)[0]
FOLDERS = [
    'contracts',
    'deployments',
    'environments',
    'tests'
]
FILES = [
    ('deployments/__init__.py',''),
    ('tests/__init__.py',''),
    ('brownie-config.json', open(BROWNIE_FOLDER+'/config.json', 'r').read())
]

if ["init", "--help"] == sys.argv[1:3]:
    sys.exit("""Usage: brownie init

This command creates the default structure for the brownie environment:

/contracts            Solidity contracts
/deployments          Python scripts relating to contract deployment
/environments         Persistent testing environment files
/tests                Python scripts for unit testing
brownie-config.json   Overrides default brownie settings""")

if sys.argv[1] == "init":
    if BROWNIE_FOLDER in os.path.abspath('.'):
        sys.exit(
            "ERROR: You cannot init the main brownie installation folder.\n"
            "Create a new folder for your project and run brownie init there.")

    if '--force' not in sys.argv and (
        os.path.exists('../brownie-config.json') or
        os.path.exists('../../brownie.config.json')
        ):
        sys.exit("ERROR: Cannot init a brownie subfolder. Use --force to override.")

init = False
for folder in [i for i in FOLDERS if not os.path.exists(i)]:
    init = True
    if sys.argv[1] == "init":
        os.mkdir(folder)

for filename, content in [i for i in FILES if not os.path.exists(i[0])]:
    init = True
    if sys.argv[1] == "init":
        open(filename,'a').write(content)

if init:
    if sys.argv[1] == "init":
        sys.exit("Brownie environment has been initiated for {}".format(os.path.abspath('.')))
    else:
        sys.exit(
            "ERROR: Brownie environment has not been initiated for this folder.\n"
            "Type 'brownie init' to create the file structure.")
elif sys.argv[1] == "init":
    sys.exit("ERROR: Brownie was already initiated in this folder.")