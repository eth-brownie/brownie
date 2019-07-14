#!/usr/bin/python3

from docopt import docopt

from brownie import network, project
from brownie.cli.utils.console import Console
from brownie._config import ARGV, CONFIG, update_argv_from_docopt


__doc__ = f"""Usage: brownie console [options]

Options:
  --network <name>        Use a specific network (default {CONFIG['network_defaults']['name']})
  --verbose -v            Enable verbose reporting
  --tb -t                 Show entire python traceback on exceptions
  --help -h               Display this message

Connects to the network and opens the brownie console.
"""


def main():
    args = docopt(__doc__)
    update_argv_from_docopt(args)

    project.load()
    network.connect(ARGV['network'])

    shell = Console()
    shell.interact(banner="Brownie environment is ready.", exitmsg="")
