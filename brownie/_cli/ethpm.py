#!/usr/bin/python3

import shutil

from docopt import docopt

from brownie._config import CONFIG
from brownie.exceptions import ProjectNotFound
from brownie.project import check_for_project, ethpm
from brownie.utils import color, notify

__doc__ = """Usage: brownie ethpm <command> [<arguments> ...] [options]

Commands:
  list                             List packages installed in this project
  install <uri> [overwrite=False]  Install a package in this project
  unlink <name>                    Unlink a package in this project
  remove <name>                    Remove an installed package from this project
  all                              List all locally available packages
  create                           Release a new

brownie ethpm create --name=


Options:
  --help -h              Display this message

...TODO...
"""


def main():
    args = docopt(__doc__)
    command = args["<command>"]
    if command not in ("all", "install", "list", "remove", "unlink"):
        print("Invalid command. Try brownie ethpm --help")
        return
    if command == "all":
        return _all()

    project_path = check_for_project(".")
    if project_path is None:
        raise ProjectNotFound
    if not project_path.joinpath("ethpm-config.yaml").exists():
        shutil.copy(
            CONFIG["brownie_folder"].joinpath("data/ethpm.yaml"),
            project_path.joinpath("ethpm-config.yaml"),
        )

    if command == "list":
        _list(project_path)
    if command == "install":
        _install(project_path, *args["<arguments>"])
    if command == "unlink":
        _unlink(project_path, *args["<arguments>"])
    if command == "remove":
        _remove(project_path, *args["<arguments>"])


def _all():
    for path in sorted(CONFIG["brownie_folder"].glob("data/ethpm/*")):
        package_list = sorted(path.glob("*"))
        if not package_list:
            path.unlink()
            continue
        print(f"{color['bright magenta']}erc1319://{path.name}{color}")
        for package_path in package_list:
            u = "\u2514" if package_path == package_list[-1] else "\u251c"
            versions = sorted(package_path.glob("*.json"))
            if len(versions) == 1:
                print(
                    f" {color['bright black']}{u}\u2500{color['bright white']}{package_path.stem}"
                    f"{color}@{color['bright white']}{versions[0].stem}{color}"
                )
                continue
            print(
                f" {color['bright black']}{u}\u2500{color['bright white']}"
                f"{package_path.stem}{color}"
            )
            for v in versions:
                u = "\u2514" if v == versions[-1] else "\u251c"
                print(f"   {color['bright black']}{u}\u2500{color['bright white']}{v.stem}{color}")


def _list(project_path):
    installed, modified = ethpm.get_installed_packages(project_path)
    package_list = sorted(installed + modified)
    if modified:
        notify(
            "WARNING",
            f"One or more files in {len(modified)} packages have been modified since installation.",
        )
        print("Unlink or reinstall them to silence this warning.")
        print(f"Modified packages name are highlighted in {color['bright blue']}blue{color}.\n")
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
    print(f'The "{color("bright magenta")}{name}{color}" package was installed successfully.')


def _unlink(project_path, name):
    ethpm.remove_package(project_path, name, False)
    print(f'The "{color("bright magenta")}{name}{color}" package was successfully unlinked.')


def _remove(project_path, name):
    ethpm.remove_package(project_path, name, True)
    print(f'The "{color("bright magenta")}{name}{color}" package was successfully removed.')
