import inspect
import sys
from pathlib import Path

import click

from brownie import network, project
from brownie._cli.console import cli as console_cli
from brownie._config import CONFIG
from brownie.project.scripts import _get_path, run
from brownie.utils import color


@click.command(short_help="Run a script in the `scripts/` folder")
@click.argument("filename", type=click.Path(exists=True, dir_okay=False))
@click.argument("function", default="main", type=str)
@click.option(
    "--network",
    "selected_network",
    default=CONFIG.settings["networks"]["default"],
    type=click.Choice(CONFIG.networks.keys()),
    show_default=True,
    help="Use a specific network",
)
# TODO: This doesn't do anything
@click.option(
    "--silent", default=False, is_flag=True, help="Suppress console output for transactions"
)
@click.option(
    "-I",
    "--interactive",
    default=False,
    is_flag=True,
    help="Open an interactive console when the script completes or raises",
)
@click.option(
    "-g",
    "--gas",
    "display_gas",
    default=False,
    is_flag=True,
    help="Display gas profile for function calls",
)
# TODO: This doesn't do anything
@click.option(
    "-t",
    "--traceback",
    "show_traceback",
    default=False,
    is_flag=True,
    help="Show entire python traceback on exceptions",
)
@click.pass_context
def cli(
    ctx, filename, function, selected_network, silent, interactive, display_gas, show_traceback
):
    """
    Execute FUNCTION in FILENAME (default function is `main`)

    Execute scripts for contract deployment, automation of common
    interactions, or for other needs like gas profiling.
    """

    active_project = None
    if project.check_for_project():
        active_project = project.load()
        active_project.load_config()
        click.echo(f"{active_project._name} is the active project.")

    network.connect(selected_network)

    path, _ = _get_path(filename)
    path_str = path.absolute().as_posix()

    try:
        return_value = run(filename, method_name=function or "main")
        extra_locals = {"_": return_value}
    except Exception as e:
        click.echo(color.format_tb(e))
        frame = next(
            (i.frame for i in inspect.trace()[::-1] if Path(i.filename).as_posix() == path_str),
            None,
        )
        if frame is None:
            # exception was an internal brownie issue - do not open the console
            sys.exit(1)

        # when exception occurs in the script, open console with the namespace of the failing frame
        globals_dict = {k: v for k, v in frame.f_globals.items() if not k.startswith("__")}
        extra_locals = {**globals_dict, **frame.f_locals}

    if interactive:
        ctx.forward(console_cli)
        ctx.invoke(
            console_cli, selected_network, show_traceback, ipython_args={"namespace": extra_locals}
        )
