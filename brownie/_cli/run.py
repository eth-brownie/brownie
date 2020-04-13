#!/usr/bin/python3

from brownie import network, project, run
from brownie._config import CONFIG, _update_argv_from_docopt
from brownie.exceptions import ProjectNotFound
from brownie.test.output import _print_gas_profile
from brownie.utils.docopt import docopt

__doc__ = f"""Usage: brownie run <filename> [<function>] [options]

Arguments:
  <filename>              The name of the script to run
  [<function>]            The function to call (default is main)

Options:
  --network [name]        Use a specific network (default {CONFIG.settings['networks']['default']})
  --gas -g                Display gas profile for function calls
  --tb -t                 Show entire python traceback on exceptions
  --help -h               Display this message

Use run to execute scripts for contract deployment, to automate common
interactions, or for gas profiling."""


def main():
    args = docopt(__doc__)
    _update_argv_from_docopt(args)

    if project.check_for_project():
        active_project = project.load()
        active_project.load_config()
        print(f"{active_project._name} is the active project.")
    else:
        raise ProjectNotFound

    network.connect(CONFIG.argv["network"])

    run(args["<filename>"], method_name=args["<function>"] or "main")
    if CONFIG.argv["gas"]:
        _print_gas_profile()
