#!/usr/bin/python3

import os
import shutil
import sys

from lib.components import config
CONFIG = config.CONFIG

FOLDERS = [
    'contracts',
    'deployments',
    'tests'
]
FILES = [
    ('deployments/__init__.py',''),
    ('tests/__init__.py',''),
    ('brownie-config.json', open(CONFIG['folders']['brownie']+'/config.json', 'r').read())
]

if ["init", "--help"] == sys.argv[1:3]:
    sys.exit("""Usage: brownie init [project]

Options:
  [project]  Make a copy of an existing project

Creates the default structure for the brownie environment:

build/                Compiled contracts and network data
contracts/            Solidity contracts
deployments/          Python scripts relating to contract deployment
tests/                Python scripts for unit testing
brownie-config.json   Project configuration file

You can optionally specify a project name, which deploys an already existing
project into a new folder with the same name. Existing projects can be found
at {}/projects""".format(CONFIG['folders']['brownie']))

if sys.argv[1] == "init":
    if (CONFIG['folders']['brownie'] in os.path.abspath('.') and 
        CONFIG['folders']['brownie']+"/projects/" not in os.path.abspath('.')):
        sys.exit(
            "ERROR: Cannot init inside the main brownie installation folder.\n"
            "Create a new folder for your project and run brownie init there.")

    if CONFIG['folders']['project'] != os.path.abspath('.'):
        if '--force' not in sys.argv:
            sys.exit("ERROR: Cannot init the subfolder of an existing brownie"
                     " project. Use --force to override.")
        CONFIG['folders']['project'] = os.path.abspath('.')

    if len(sys.argv) > 2:
        folder = CONFIG['folders']['brownie'] + '/projects/' + sys.argv[2]
        if not os.path.exists(folder):
            sys.exit("ERROR: No project exists with the name '{}'.".format(sys.argv[2]))
        try:
            shutil.copytree(folder, sys.argv[2])
        except FileExistsError:
            sys.exit("ERROR: One or more files for this project already exist.")
        sys.exit("Project was created in ./{}".format(sys.argv[2]))

def _fullpath(f):
    return "{}/{}".format(CONFIG['folders']['project'], f)

init = False
for folder in [i for i in FOLDERS if not os.path.exists(_fullpath(i))]:
    init = True
    if sys.argv[1] == "init":
        os.mkdir(_fullpath(folder))

for filename, content in [i for i in FILES if not os.path.exists(_fullpath(i[0]))]:
    init = True
    if sys.argv[1] == "init":
        open(_fullpath(filename), 'a').write(content)

if init:
    if sys.argv[1] == "init":
        sys.exit("Brownie environment has been initiated for {}".format(
            os.path.abspath('.')))
    else:
        sys.exit(
            "ERROR: Brownie environment has not been initiated for this folder."
            "\nType 'brownie init' to create the file structure.")
elif sys.argv[1] == "init":
    sys.exit("ERROR: Brownie was already initiated in this folder.")

for folder in ('build', 'build/contracts','build/networks'):
    folder = "{}/{}".format(CONFIG['folders']['project'],folder)
    if not os.path.exists(folder):
        os.mkdir(folder)