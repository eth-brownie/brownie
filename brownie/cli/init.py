#!/usr/bin/python3

from docopt import docopt
import os
from pathlib import Path
import shutil
import sys

import brownie.project as project
import brownie.config as config
CONFIG = config.CONFIG



__doc__ = """Usage: brownie init [<project>] [options]

Arguments:
  <project>           Make a copy of an existing project

Options:
  --help              Display this message

brownie init is used to create new brownie projects. It creates the default
structure for the brownie environment:

build/                Compiled contracts and network data
contracts/            Solidity contracts
scripts/              Python scripts that are not for testing
tests/                Python scripts for unit testing
brownie-config.json   Project configuration file

You can optionally specify a project name, which deploys an already existing
project into a new folder with the same name. Existing projects can be found
at {}/projects
""".format(CONFIG['folders']['brownie'])


def main():
    args = docopt(__doc__)
    
    if CONFIG['folders']['brownie'] in str(Path('.').resolve()):
        sys.exit(
            "ERROR: Cannot init inside the main brownie installation folder.\n"
            "Create a new folder for your project and run brownie init there.")

    # TODO - remote packages
    # if args['<project>']:
    #     folder = CONFIG['folders']['brownie'] + "/projects/" + args['<project>']
    #     if not os.path.exists(folder):
    #         sys.exit("ERROR: No project exists with the name '{}'".format(args['<project>']))
    #     try:
    #         shutil.copytree(folder, args['<project>'])
    #     except FileExistsError:
    #         sys.exit("ERROR: One or more files for this project already exist.")
    #     if not os.path.exists(args['<project>']+"/brownie-config.json"):
    #         shutil.copyfile(
    #             CONFIG['folders']['brownie']+'/config.json',
    #             args['<project>']+"/brownie-config.json"
    #         )
    #     print("Project was created in ./{}".format(args['<project>']))
    #     sys.exit()

    project.new('.', config.ARGV['force'])
    print("Brownie environment has been initiated.")
    sys.exit()