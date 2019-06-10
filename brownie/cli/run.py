#!/usr/bin/python3

from docopt import docopt

from brownie import network
from brownie.test.main import run_script
from brownie._config import ARGV, CONFIG


__doc__ = """Usage: brownie run <filename> [<function>] [options]

Arguments:
  <filename>              The name of the script to run
  [<function>]            The function to call (default is main)

Options:
  --network [name]        Use a specific network (default {})
  --gas -g                Display gas profile for function calls
  --verbose -v            Enable verbose reporting
  --tb -t                 Show entire python traceback on exceptions
  --help -h               Display this message

Use run to execute scripts for contract deployment, to automate common
interactions, or for gas profiling.""".format(CONFIG['network_defaults']['name'])


def main():
    args = docopt(__doc__)
    ARGV._update_from_args(args)
    network.connect(ARGV['network'])
    run_script(args['<filename>'], args['<function>'] or "main", gas_profile=ARGV['gas'])
