import click

from brownie import project
from brownie.utils import notify


@click.command(short_help="Initialize a new brownie project")
@click.argument("mix", type=str)
@click.option(
    "--path",
    default=None,
    help="Path to initialize (default is the name of the mix)",
)
@click.option("--force", default=False, is_flag=True, help="Allow init inside a project subfolder")
def cli(mix, path, force):
    """
    Initialize this project using MIX as a template.

    Brownie mixes are ready-made templates that you can use as a starting
    point for your own project, or as a part of a tutorial.

    For a complete list of Brownie mixes visit https://www.github.com/brownie-mixes
    """
    if not path:
        path = mix
    path = project.from_brownie_mix(mix, path, force)
    notify("SUCCESS", f"Brownie mix '{mix}' has been initiated at {path}")
