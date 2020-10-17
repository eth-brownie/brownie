import sys

import click
import IPython
from IPython.terminal.ipapp import load_default_config

import brownie
from brownie import network, project
from brownie._config import CONFIG

_parser_cache: dict = {}


@click.command(short_help="Load the console", context_settings=dict(ignore_unknown_options=True))
@click.option(
    "--network",
    "selected_network",
    default=CONFIG.settings["networks"]["default"],
    type=click.Choice(CONFIG.networks.keys()),
    show_default=True,
    help="Use a specific network",
)
@click.option(
    "-t",
    "--traceback",
    "show_traceback",
    default=False,
    is_flag=True,
    help="Show entire python traceback on exceptions",
)
@click.argument("ipython_args", nargs=-1, type=click.UNPROCESSED)
def cli(selected_network, show_traceback, ipython_args):
    """
    Connects to the selected network and opens the brownie console.
    """
    if project.check_for_project():
        active_project = project.load()
        active_project.load_config()
    else:
        active_project = None

    network.connect(selected_network)

    return console(active_project, ipython_args=ipython_args)


def console(active_project, extra_locals=None, ipython_args=None):

    project_name = active_project._name if hasattr(active_project, "_name") else "No active Project"

    config = load_default_config()
    config.TerminalInteractiveShell.banner1 = f"""
  Python {sys.version.split(" ")[0]} on {sys.platform}
  IPython: {IPython.__version__}

  Brownie {brownie._config.__version__}
  Project: {project_name}
    """

    namespace = {component: getattr(brownie, component) for component in brownie.__all__}
    namespace.update(**active_project)
    if extra_locals:
        namespace.update(extra_locals)

    return IPython.start_ipython(argv=ipython_args, user_ns=namespace, config=config)
