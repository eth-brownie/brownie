import shutil
from pathlib import Path

import click

from brownie import project
from brownie._config import _get_data_folder
from brownie.utils import color, notify


@click.group(short_help="Install and manage external packages")
def cli():
    """
    Manager for packages installed from ethPM and Github. Installed packages can
    be added as dependencies and imported into your own projects.

    See https://eth-brownie.readthedocs.io/en/stable/package-manager.html for
    more information on how to install and use packages.
    """


@cli.command(short_help="List installed packages")
def list():
    org_names = []
    for path in _get_data_folder().joinpath("packages").iterdir():
        if not path.is_dir():
            continue
        elif not any(i for i in path.iterdir() if i.is_dir() and "@" in i.name):
            shutil.rmtree(path)
        else:
            org_names.append(path)

    if not org_names:
        print("No packages are currently installed.")
    else:
        print("The following packages are currently installed:")

    for org_path in org_names:
        packages = [p for p in org_path.iterdir()]
        print(f"\n{color('bright magenta')}{org_path.name}{color}")
        for path in packages:
            u = "\u2514" if path == packages[-1] else "\u251c"
            name, version = path.name.rsplit("@", maxsplit=1)
            print(f" {color('bright black')}{u}\u2500{_format_pkg(org_path.name, name, version)}")


@cli.command(short_help="Make a copy of an installed package")
@click.argument("package_id")
@click.argument("path", default=".")
def clone(package_id, path):
    """
    Copy PACKAGE_ID to PATH

    Default PATH is local directory
    """
    org, repo, version = _split_id(package_id)
    source_path = _get_data_folder().joinpath(f"packages/{org}/{repo}@{version}")
    if not source_path.exists():
        raise FileNotFoundError(f"Package '{_format_pkg(org, repo, version)}' is not installed")
    dest_path = Path(path)
    if dest_path.exists():
        if not dest_path.is_dir():
            raise FileExistsError("Destination path already exists")
        dest_path = dest_path.joinpath(package_id)
    shutil.copytree(source_path, dest_path)
    notify("SUCCESS", f"Package '{_format_pkg(org, repo, version)}' was cloned at {dest_path}")


@cli.command(short_help="Delete an installed package")
@click.argument("package_id")
def delete(package_id):
    """
    Deletes PACKAGE_ID from installed pacakges
    """
    org, repo, version = _split_id(package_id)
    source_path = _get_data_folder().joinpath(f"packages/{org}/{repo}@{version}")
    if not source_path.exists():
        raise FileNotFoundError(f"Package '{_format_pkg(org, repo, version)}' is not installed")
    shutil.rmtree(source_path)
    notify("SUCCESS", f"Package '{_format_pkg(org, repo, version)}' has been deleted")


@cli.command(short_help="Install a new package")
@click.argument("uri")
def install(uri):
    """
    Installs package from URI
    """
    package_id = project.main.install_package(uri)
    org, repo, version = _split_id(package_id)
    notify("SUCCESS", f"Package '{_format_pkg(org, repo, version)}' has been installed")


def _split_id(package_id):
    try:
        path, version = package_id.split("@")
        org, repo = path.split("/")
        return org, repo, version
    except ValueError:
        raise ValueError(
            "Invalid package ID. Must be given as [ORG]/[REPO]@[VERSION]"
            f"\ne.g. {_format_pkg('openzeppelin', 'openzeppelin-contracts', 'v2.5.0')}"
        ) from None


def _format_pkg(org, repo, version):
    return (
        f"{color('blue')}{org}/{color('bright blue')}{repo}"
        f"{color('blue')}@{color('bright blue')}{version}{color}"
    )
