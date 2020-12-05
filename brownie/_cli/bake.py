#!/usr/bin/python3

from brownie import project
from brownie.utils import notify
from brownie.utils.docopt import docopt

__doc__ = """Usage: brownie bake <mix> [<path>] [options]

Arguments:
  <mix>                 Name of Brownie mix to initialize
  <path>                Path to initialize to (default is name of mix)

Options:
  --force -f            Allow init inside a project subfolder
  --help -h             Display this message

Brownie mixes are ready-made templates that you can use as a starting
point for your own project, or as a part of a tutorial.

For a complete list of Brownie mixes visit https://www.github.com/brownie-mix
"""


def main():
    args = docopt(__doc__)
    path = project.from_brownie_mix(args["<mix>"], args["<path>"], args["--force"])
    notify("SUCCESS", f"Brownie mix '{args['<mix>']}' has been initiated at {path}")
