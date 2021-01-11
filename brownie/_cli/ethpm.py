import json
import shutil

import click
import yaml

from brownie import accounts, network
from brownie._config import BROWNIE_FOLDER, _get_data_folder
from brownie.exceptions import ProjectNotFound, UnknownAccount
from brownie.project import check_for_project, ethpm
from brownie.utils import color, notify


@click.group(short_help="Install, manage, and create ethPM manifests")
def cli():
    """
    ethPM is a decentralized package manager used to distribute EVM smart contracts
    and projects.

    See https://eth-brownie.readthedocs.io/en/stable/ethpm.html for more
    information on how to use it within Brownie.
    """
    project_path = check_for_project(".")
    if project_path is None:
        raise ProjectNotFound
    if not project_path.joinpath("ethpm-config.yaml").exists():
        shutil.copy(
            BROWNIE_FOLDER.joinpath("data/ethpm-config.yaml"),
            project_path.joinpath("ethpm-config.yaml"),
        )


@cli.command(name="list", short_help="List installed packages")
def _list():
    project_path = check_for_project(".")
    installed, modified = ethpm.get_installed_packages(project_path)
    package_list = sorted(installed + modified)
    if not package_list:
        print("No packages are currently installed in this project.")
        return
    if modified:
        notify(
            "WARNING",
            f"One or more files in {len(modified)} packages have been modified since installation.",
        )
        print("Unlink or reinstall them to silence this warning.")
        print(f"Modified packages name are highlighted in {color('bright blue')}blue{color}.\n")
    print(f"Found {color('bright magenta')}{len(package_list)}{color} installed packages:")
    for name in package_list:
        u = "\u2514" if name == package_list[-1] else "\u251c"
        c = color("bright blue") if name in modified else color("bright white")
        print(
            f" {color('bright black')}{u}\u2500{c}{name[0]}{color}@"
            f"{color('bright white')}{name[1]}{color}"
        )


@cli.command(short_help="Install a new package")
@click.argument("uri")
@click.option(
    "-R",
    "--replace",
    default=False,
    is_flag=True,
    help="Overwrite the previously installed package of same name",
)
def install(uri, replace):
    """
    Install package from EthPM v2 (ERC1319) compliant URI
    """
    project_path = check_for_project(".")
    if replace:
        if replace.lower() not in ("true", "false"):
            raise ValueError("Invalid command for 'overwrite', must be True or False")
        replace = eval(replace.capitalize())
    print(f'Attempting to install package at "{color("bright magenta")}{uri}{color}"...')
    name = ethpm.install_package(project_path, uri, replace)
    notify("SUCCESS", f'The "{color("bright magenta")}{name}{color}" package was installed.')


@cli.command(short_help="Unlink an installed package")
@click.argument("name")
def unlink(name):
    project_path = check_for_project(".")
    if ethpm.remove_package(project_path, name, False):
        notify("SUCCESS", f'The "{color("bright magenta")}{name}{color}" package was unlinked.')
        return
    notify("ERROR", f'"{color("bright magenta")}{name}{color}" is not installed in this project.')


@cli.command(short_help="Remove an installed package")
@click.argument("name")
def remove(name):
    project_path = check_for_project(".")
    if ethpm.remove_package(project_path, name, True):
        notify("SUCCESS", f'The "{color("bright magenta")}{name}{color}" package was removed.')
        return
    notify("ERROR", f'"{color("bright magenta")}{name}{color}" is not installed in this project.')


@cli.command(short_help="Generate a manifest")
@click.option(
    "-p",
    "--path",
    "manifest_pathstr",
    default="manifest.json",
    type=click.Path(exists=False, dir_okay=False),
)
def create(manifest_pathstr):
    project_path = check_for_project(".")
    print("Generating a manifest based on configuration settings in ethpm-config.yaml...")
    with project_path.joinpath("ethpm-config.yaml").open() as fp:
        project_config = yaml.safe_load(fp)
    try:
        manifest = ethpm.create_manifest(project_path, project_config)[0]
    except Exception as e:
        notify("ERROR", f"{type(e).__name__}: {e}")
        print("Ensure that all package configuration settings are correct in ethpm-config.yaml")
        return
    with project_path.joinpath(manifest_pathstr).open("w") as fp:
        json.dump(manifest, fp, sort_keys=True, indent=2)
    notify(
        "SUCCESS",
        f'Generated manifest saved as "{color("bright magenta")}{manifest_pathstr}{color}"',
    )


@cli.command(short_help="Generate a manifest and publish to an ethPM registry")
@click.argument("registry")
@click.argument("sender")
def release(registry, sender):
    project_path = check_for_project(".")
    network.connect("mainnet")
    with project_path.joinpath("ethpm-config.yaml").open() as fp:
        project_config = yaml.safe_load(fp)
    print("Generating manifest and pinning assets to IPFS...")
    manifest, uri = ethpm.create_manifest(project_path, project_config, True, False)
    if sender in accounts:
        account = accounts.at(sender)
    else:
        try:
            account = accounts.load(sender)
        except FileNotFoundError:
            raise UnknownAccount(f"Unknown account '{sender}'")
    name = f'{manifest["package_name"]}@{manifest["version"]}'
    print(f'Releasing {name} on "{registry}"...')
    try:
        tx = ethpm.release_package(
            registry, account, manifest["package_name"], manifest["version"], uri
        )
        if tx.status == 1:
            notify("SUCCESS", f"{name} has been released!")
            print(f"\nURI: {color('bright magenta')}ethpm://{registry}:1/{name}{color}")
            return
    except Exception:
        pass
    notify("ERROR", f'Transaction reverted when releasing {name} on "{registry}"')


@cli.command(short_help="List all locally available packages")
def all():
    ethpm_folder = _get_data_folder().joinpath("ethpm")
    if not list(ethpm_folder.glob("*")):
        print("No local packages are currently available.")
    for path in sorted(ethpm_folder.glob("*")):
        package_list = sorted(path.glob("*"))
        if not package_list:
            path.unlink()
            continue
        print(f"{color('bright magenta')}ethpm://{path.name}{color}")
        for package_path in package_list:
            u = "\u2514" if package_path == package_list[-1] else "\u251c"
            versions = sorted(package_path.glob("*.json"))
            if len(versions) == 1:
                print(
                    f" {color('bright black')}{u}\u2500{color('bright white')}{package_path.stem}"
                    f"{color}@{color('bright white')}{versions[0].stem}{color}"
                )
                continue
            print(
                f" {color('bright black')}{u}\u2500{color('bright white')}"
                f"{package_path.stem}{color}"
            )
            for v in versions:
                u = "\u2514" if v == versions[-1] else "\u251c"
                print(f"   {color('bright black')}{u}\u2500{color('bright white')}{v.stem}{color}")
