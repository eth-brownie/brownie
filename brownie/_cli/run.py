#!/usr/bin/python3

import inspect
import sys
from pathlib import Path

from brownie import network, project
from brownie._cli.console import Console
from brownie._config import CONFIG, _update_argv_from_docopt
from brownie.project.scripts import _get_path, run
from brownie.test.output import _build_gas_profile_output
from brownie.utils import color
from brownie.utils.docopt import docopt

__doc__ = f"""Usage: brownie run <filename> [<function>] [options]

Arguments:
  <filename>              The name of the script to run
  [<function>]            The function to call (default is main)

Options:
  --network [name]        Use a specific network (default {CONFIG.settings['networks']['default']})
  --silent                Suppress console output for transactions
  --interactive -I        Open an interactive console when the script completes or raises
  --gas -g                Display gas profile for function calls
  --tb -t                 Show entire python traceback on exceptions
  --help -h               Display this message

Use run to execute scripts for contract deployment, to automate common
interactions, or for gas profiling."""


def main():
    args = docopt(__doc__)
    _update_argv_from_docopt(args)

    active_project = None
    if project.check_for_project():
        active_project = project.load()
        active_project.load_config()
        print(f"{active_project._name} is the active project.")

    network.connect(CONFIG.argv["network"])

    path, _ = _get_path(args["<filename>"])
    path_str = path.absolute().as_posix()

    try:
        return_value = run(args["<filename>"], method_name=args["<function>"] or "main")
        exit_code = 0
        extra_locals = {"_": return_value}
    except Exception as e:
        print(color.format_tb(e))
        frame = next(
            (i.frame for i in inspect.trace()[::-1] if Path(i.filename).as_posix() == path_str),
            None,
        )
        if frame is None:
            # exception was an internal brownie issue - do not open the console
            sys.exit(1)

        # when exception occurs in the script, open console with the namespace of the failing frame
        exit_code = 1
        globals_dict = {k: v for k, v in frame.f_globals.items() if not k.startswith("__")}
        extra_locals = {**globals_dict, **frame.f_locals}

    try:
        if args["--interactive"]:
            shell = Console(active_project, extra_locals)
            shell.interact(banner="\nInteractive mode enabled. Use quit() to close.", exitmsg="")
    finally:
        # the console terminates from a SystemExit - make sure we still deliver the final gas report
        if CONFIG.argv["gas"]:
            print("\n======= Gas profile =======")
            for line in _build_gas_profile_output():
                print(line)

        sys.exit(exit_code)
