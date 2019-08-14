#!/usr/bin/python3

from docopt import docopt

from brownie import network, project
from brownie.cli.utils.console import Console
from brownie._config import ARGV, CONFIG, update_argv_from_docopt


__doc__ = f"""Usage: brownie console [options]

Options:
  --network <name>        Use a specific network (default {CONFIG['network']['default']})
  --tb -t                 Show entire python traceback on exceptions
  --help -h               Display this message

Connects to the network and opens the brownie console.
"""


def main():
    args = docopt(__doc__)
    update_argv_from_docopt(args)

    if project.check_for_project():
        p = project.load()
        p.load_config()
        print(f"{p._name} is the active project.")
    else:
        p = None
        print("No active project loaded.")

    network.connect(ARGV['network'])

    shell = Console(p)
    shell.interact(banner="Brownie environment is ready.", exitmsg="")
