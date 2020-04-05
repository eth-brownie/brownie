#!/usr/bin/python3

import json
import shutil
import sys

import yaml

from brownie import accounts, network
from brownie._config import BROWNIE_FOLDER, _get_data_folder
from brownie.exceptions import ProjectNotFound, UnknownAccount
from brownie.project import check_for_project, ethpm
from brownie.utils import color, notify
from brownie.utils.docopt import docopt

__doc__ = """Usage: brownie ethpm <command> [<arguments> ...] [options]

Commands:
  list                             List installed packages
  install <uri> [overwrite=False]  Install a new package
  unlink <name>                    Unlink an installed package
  remove <name>                    Remove an installed package
  create [filename]                Generate a manifest
  release <registry> <account>     Generate a manifest and publish to an ethPM registry
  all                              List all locally available packages

Options:
  --help -h                        Display this message

ethPM is a decentralized package manager used to distribute EVM smart contracts
and projects. See https://eth-brownie.readthedocs.io/en/stable/ethpm.html for more
information on how to use it within Brownie.
"""


def main():
    args = docopt(__doc__)
    try:
        fn = getattr(sys.modules[__name__], f"_{args['<command>']}")
    except AttributeError:
        print("Invalid command. Try brownie ethpm --help")
        return
    project_path = check_for_project(".")
    if project_path is None:
        raise ProjectNotFound
    if not project_path.joinpath("ethpm-config.yaml").exists():
        shutil.copy(
            BROWNIE_FOLDER.joinpath("data/ethpm-config.yaml"),
            project_path.joinpath("ethpm-config.yaml"),
        )
    try:
        fn(project_path, *args["<arguments>"])
    except TypeError:
        print(f"Invalid arguments for command '{args['<command>']}'. Try brownie ethpm --help")
        return


def _list(project_path):
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


def _install(project_path, uri, replace=False):
    if replace:
        if replace.lower() not in ("true", "false"):
            raise ValueError("Invalid command for 'overwrite', must be True or False")
        replace = eval(replace.capitalize())
    print(f'Attempting to install package at "{color("bright magenta")}{uri}{color}"...')
    name = ethpm.install_package(project_path, uri, replace)
    notify("SUCCESS", f'The "{color("bright magenta")}{name}{color}" package was installed.')


def _unlink(project_path, name):
    if ethpm.remove_package(project_path, name, False):
        notify("SUCCESS", f'The "{color("bright magenta")}{name}{color}" package was unlinked.')
        return
    notify("ERROR", f'"{color("bright magenta")}{name}{color}" is not installed in this project.')


def _remove(project_path, name):
    if ethpm.remove_package(project_path, name, True):
        notify("SUCCESS", f'The "{color("bright magenta")}{name}{color}" package was removed.')
        return
    notify("ERROR", f'"{color("bright magenta")}{name}{color}" is not installed in this project.')


def _create(project_path, manifest_pathstr="manifest.json"):
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


def _release(project_path, registry_address, sender):
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
    print(f'Releasing {name} on "{registry_address}"...')
    try:
        tx = ethpm.release_package(
            registry_address, account, manifest["package_name"], manifest["version"], uri
        )
        if tx.status == 1:
            notify("SUCCESS", f"{name} has been released!")
            print(f"\nURI: {color('bright magenta')}ethpm://{registry_address}:1/{name}{color}")
            return
    except Exception:
        pass
    notify("ERROR", f'Transaction reverted when releasing {name} on "{registry_address}"')


def _all(project_path):
    ethpm_folder = _get_data_folder().joinpath("ethpm")
    print(
        f"Visit {color('bright magenta')}https://explorer.ethpm.com/{color}"
        " for a list of ethPM registries and packages.\n"
    )
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
