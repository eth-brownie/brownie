import click

from brownie import project
from brownie.utils import notify


@click.command(short_help="Initialize a new brownie project")
@click.option(
    "--path", default=".", help="Path to initialize (default is the current path)",
)
@click.option(
    "--force",
    default=False,
    is_flag=True,
    help="Allow initialization inside a directory that is not empty, "
    "or a subdirectory of an existing project",
)
def cli(path, force):
    """
    brownie init is used to create new brownie projects. It creates the default
    structure for the brownie environment:

        build/          Compiled contracts and test data
        contracts/      Contract source code
        interfaces/     Interface source code
        reports/        Report files for contract analysis
        scripts/        Scripts for deployment and interaction
        tests/          Scripts for project testing

    """
    path = project.new(path, ignore_subfolder=force, ignore_existing=force)
    notify("SUCCESS", f"A new Brownie project has been initialized at {path}")
