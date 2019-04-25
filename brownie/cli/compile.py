#!/usr/bin/python3

from docopt import docopt
from pathlib import Path
import shutil

import brownie.project as project
import brownie._config as config


__doc__ = """Usage: brownie compile [options]

Options:
  --all -a              Recompile all contracts
  --help -h             Display this message

Compiles the contract source files for this project and saves the results
in the build/contracts folder."""


def main():
    args = docopt(__doc__)
    project_path = project.check_for_project('.')
    build_path = project_path.joinpath('build/contracts')
    if config.ARGV['all']:
        shutil.rmtree(build_path, ignore_errors=True)
    project.load(project_path)
    print("Brownie project has been compiled at {}".format(build_path))
