#!/usr/bin/python3

import shutil

from docopt import docopt

from brownie import project
from brownie.exceptions import ProjectNotFound

__doc__ = """Usage: brownie compile [options]

Options:
  --all -a              Recompile all contracts
  --help -h             Display this message

Compiles the contract source files for this project and saves the results
in the build/contracts folder."""


def main():
    args = docopt(__doc__)
    project_path = project.check_for_project(".")
    if project_path is None:
        raise ProjectNotFound
    build_path = project_path.joinpath("build/contracts")
    if args["--all"]:
        shutil.rmtree(build_path, ignore_errors=True)
    project.load(project_path)
    print(f"Brownie project has been compiled at {build_path}")
