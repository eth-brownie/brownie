#!/usr/bin/python3

import inspect
from pathlib import Path

from brownie import network, project
from brownie._cli.console import Console
from brownie._config import CONFIG, _update_argv_from_docopt
from brownie.exceptions import ProjectNotFound
from brownie.project.scripts import _get_path, run
from brownie.test.output import _print_gas_profile
from brownie.utils import color
from brownie.utils.docopt import docopt

__doc__ = f"""Usage: brownie run <filename> [<function>] [options]

Arguments:
  <filename>              The name of the script to run
  [<function>]            The function to call (default is main)

Options:
  --network [name]        Use a specific network (default {CONFIG.settings['networks']['default']})
  --interactive -I        Open an interactive console if the script fails
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

    path, _ = _get_path(args["<filename>"])
    path_str = path.absolute().as_posix()

    try:
        run(args["<filename>"], method_name=args["<function>"] or "main")
    except Exception as e:
        print(color.format_tb(e))

        if args["--interactive"]:
            frame = next(
                (i.frame for i in inspect.trace() if Path(i.filename).as_posix() == path_str), None
            )
            if frame is not None:
                globals_dict = {k: v for k, v in frame.f_globals.items() if not k.startswith("__")}

                shell = Console(active_project, {**globals_dict, **frame.f_locals})
                shell.interact(
                    banner=f"\nInteractive mode enabled. Use quit() to close.", exitmsg=""
                )

    if CONFIG.argv["gas"]:
        _print_gas_profile()
