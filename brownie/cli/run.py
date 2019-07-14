#!/usr/bin/python3

from docopt import docopt

from brownie import network, project, run
from brownie._config import ARGV, CONFIG, update_argv_from_docopt


__doc__ = f"""Usage: brownie run <filename> [<function>] [options]

Arguments:
  <filename>              The name of the script to run
  [<function>]            The function to call (default is main)

Options:
  --network [name]        Use a specific network (default {CONFIG['network_defaults']['name']})
  --gas -g                Display gas profile for function calls
  --verbose -v            Enable verbose reporting
  --tb -t                 Show entire python traceback on exceptions
  --help -h               Display this message

Use run to execute scripts for contract deployment, to automate common
interactions, or for gas profiling."""


def main():
    args = docopt(__doc__)
    update_argv_from_docopt(args)
    project.load()
    network.connect(ARGV['network'])
    run(args['<filename>'], args['<function>'] or "main", gas_profile=ARGV['gas'])
