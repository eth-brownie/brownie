#!/usr/bin/python3

from docopt import docopt
import os
import shutil
import sys

from lib.services import config
CONFIG = config.CONFIG


FOLDERS = ["contracts", "deployments", "tests"]
BUILD_FOLDERS = ["build", "build/contracts", "build/networks"]
FILES = [
    ("deployments/__init__.py", ""),
    ("tests/__init__.py", ""),
    (
        "brownie-config.json",
        open(CONFIG['folders']['brownie']+"/config.json", 'r').read()
    )
]

__doc__ = """Usage: brownie init [<project>] [options]

Arguments:
  <project>           Make a copy of an existing project

Options:
  --help              Display this message

brownie init is used to create new brownie projects. It creates the default
structure for the brownie environment:

build/                Compiled contracts and network data
contracts/            Solidity contracts
deployments/          Python scripts relating to contract deployment
tests/                Python scripts for unit testing
brownie-config.json   Project configuration file

You can optionally specify a project name, which deploys an already existing
project into a new folder with the same name. Existing projects can be found
at {}/projects
""".format(CONFIG['folders']['brownie'])


def main():
    args = docopt(__doc__)
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

    if check_for_project():
        sys.exit("ERROR: Brownie was already initiated in this folder.")

    if args['<project>']:
        folder = CONFIG['folders']['brownie'] + "/projects/" + args['<project>']
        if not os.path.exists(folder):
            sys.exit("ERROR: No project exists with the name '{}'".format(args['<project>']))
        try:
            shutil.copytree(folder, args['<project>'])
        except FileExistsError:
            sys.exit("ERROR: One or more files for this project already exist.")
        if not os.path.exists(args['<project>']+"/brownie-config.json"):
            shutil.copyfile(
                CONFIG['folders']['brownie']+'/config.json',
                args['<project>']+"/brownie-config.json"
            )
        sys.exit("Project was created in ./{}".format(args['<project>']))
    
    create_project()
    create_build_folders()
    sys.exit("Brownie environment has been initiated.")


def check_for_project():
    os.chdir(CONFIG['folders']['project'])
    if [i for i in FOLDERS if not os.path.exists(i)]:
        return False
    if [i for i in FILES if not os.path.exists(i[0])]:
        return False
    return True

def create_project():
    os.chdir(CONFIG['folders']['project'])
    for folder in [i for i in FOLDERS if not os.path.exists(i)]:
        os.mkdir(folder)
    for filename, content in [i for i in FILES if not os.path.exists(i[0])]:
        open(filename, 'w').write(content)

def create_build_folders():
    for folder in [i for i in BUILD_FOLDERS if not os.path.exists(i)]:
        os.mkdir(folder)