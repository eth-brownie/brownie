#!/usr/bin/python3

from docopt import docopt
from pathlib import Path

import brownie
from brownie import network, project
from brownie.test.main import run_script
from brownie.cli.utils.console import Console
from brownie._config import ARGV, CONFIG


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
    ARGV._update_from_args(args)

    project.load()
    network.connect(ARGV['network'])

    console_dict = dict((i, getattr(brownie, i)) for i in brownie.__all__)
    console_dict['run'] = run_script
    del console_dict['project']

    shell = Console(console_dict, Path(CONFIG['folders']['project']).joinpath('.history'))
    shell.interact(banner="Brownie environment is ready.", exitmsg="")
