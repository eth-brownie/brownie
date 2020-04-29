#!/usr/bin/python3

import shutil

from brownie import project
from brownie.exceptions import ProjectNotFound
from brownie.utils.docopt import docopt

__doc__ = """Usage: brownie compile [options]

Options:
  --all -a              Recompile all contracts
  --help -h             Display this message

Compiles the contract source files for this project and saves the results
in the build/contracts/ folder.

Note that Brownie automatically recompiles any changed contracts each time
a project is loaded. You do not have to manually trigger a recompile."""


def main():
    args = docopt(__doc__)
    project_path = project.check_for_project(".")
    if project_path is None:
        raise ProjectNotFound
    contract_artifact_path = project_path.joinpath("build/contracts")
    interface_artifact_path = project_path.joinpath("build/interfaces")
    if args["--all"]:
        shutil.rmtree(contract_artifact_path, ignore_errors=True)
        shutil.rmtree(interface_artifact_path, ignore_errors=True)
    project.load(project_path)
    print(f"Project has been compiled. Build artifacts saved at {contract_artifact_path}")
