#!/usr/bin/python3

import json
import shutil
import sys
from pathlib import Path

from brownie import accounts
from brownie._config import _get_data_folder
from brownie.convert import to_address
from brownie.utils import color, notify
from brownie.utils.docopt import docopt

__doc__ = """Usage: brownie accounts <command> [<arguments> ...] [options]

Commands:
  list                             List available accounts
  new <id>                         Add a new account by entering a private key
  generate <id>                    Add a new account with a random private key
  import <id> <path>               Import a new account via a keystore file
  export <id> <path>               Export an existing account keystore file
  password <id>                    Change the password of an existing account
  delete <id>                      Delete an existing account

Options:
  --help -h                        Display this message

Command-line helper for managing local accounts. You can unlock local accounts from
scripts or the console using the Accounts.load method.
"""


def main():
    args = docopt(__doc__)
    try:
        fn = getattr(sys.modules[__name__], f"_{args['<command>']}")
    except AttributeError:
        print("Invalid command. Try brownie accounts --help")
        return
    try:
        fn(*args["<arguments>"])
    except TypeError:
        print(f"Invalid arguments for command '{args['<command>']}'. Try brownie accounts --help")
        return


def _list():
    account_paths = sorted(_get_data_folder().glob("accounts/*.json"))
    print(f"Found {len(account_paths)} account{'s' if len(account_paths)!=1 else ''}:")
    for path in account_paths:
        u = "\u2514" if path == account_paths[-1] else "\u251c"
        with path.open() as fp:
            data = json.load(fp)
        print(
            f" {color('bright black')}{u}\u2500{color('bright blue')}{path.stem}{color}"
            f": {color('bright magenta')}{to_address(data['address'])}{color}"
        )


def _new(id_):
    pk = input("Enter the private key you wish to add: ")
    a = accounts.add(pk)
    a.save(id_)
    notify(
        "SUCCESS",
        f"A new account '{color('bright magenta')}{a.address}{color}'"
        f" has been generated with the id '{color('bright blue')}{id_}{color}'",
    )


def _generate(id_):
    print("Generating a new private key...")
    a = accounts.add()
    a.save(id_)
    notify(
        "SUCCESS",
        f"A new account '{color('bright magenta')}{a.address}{color}'"
        f" has been generated with the id '{color('bright blue')}{id_}{color}'",
    )


def _import(id_, path):
    dest_path = _get_data_folder().joinpath(f"accounts/{id_}.json")
    if dest_path.exists():
        raise FileExistsError(f"A keystore file already exists with the id '{id_}'")

    source_path = Path(path).absolute()
    if not source_path.exists():
        temp_source = source_path.with_suffix(".json")
        if temp_source.exists():
            source_path = temp_source
        else:
            raise FileNotFoundError(f"Cannot find {source_path}")

    accounts.load(source_path)
    shutil.copy(source_path, dest_path)
    notify(
        "SUCCESS",
        f"Keystore '{color('bright magenta')}{source_path}{color}'"
        f" has been imported with the id '{color('bright blue')}{id_}{color}'",
    )


def _export(id_, path):
    source_path = _get_data_folder().joinpath(f"accounts/{id_}.json")
    if not source_path.exists():
        raise FileNotFoundError(f"No keystore exists with the id '{id_}'")
    dest_path = Path(path).absolute()
    if not dest_path.suffix:
        dest_path = dest_path.with_suffix(".json")
    if dest_path.exists():
        raise FileExistsError(f"Export path {dest_path} already exists")
    shutil.copy(source_path, dest_path)
    notify(
        "SUCCESS",
        f"Account with id '{color('bright blue')}{id_}{color}' has been"
        f" exported to keystore '{color('bright magenta')}{dest_path}{color}'",
    )


def _password(id_):
    a = accounts.load(id_)
    a.save(id_, overwrite=True)
    notify("SUCCESS", f"Password has been changed for account '{color('bright blue')}{id_}{color}'")


def _delete(id_):
    path = _get_data_folder().joinpath(f"accounts/{id_}.json")
    path.unlink()
    notify("SUCCESS", f"Account '{color('bright blue')}{id_}{color}' has been deleted")
