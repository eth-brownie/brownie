import json
import shutil
from pathlib import Path

import click

from brownie import accounts
from brownie._config import _get_data_folder
from brownie.convert import to_address
from brownie.utils import color, notify


@click.group(short_help="Manage local accounts")
def cli():
    """
    Command-line helper for managing local accounts. You can unlock local accounts from
    scripts or the console using the Accounts.load() method.
    """


# Different name because `list` is a keyword
@cli.command(name="list", short_help="List available accounts")
def _list():
    account_paths = sorted(_get_data_folder().glob("accounts/*.json"))
    if len(account_paths) == 0:
        print("No accounts found.")
    else:
        print(f"Found {len(account_paths)} account{'s' if len(account_paths)!=1 else ''}:")
        for path in account_paths:
            u = "\u2514" if path == account_paths[-1] else "\u251c"
            with path.open() as fp:
                data = json.load(fp)
            print(
                f" {color('bright black')}{u}\u2500{color('bright blue')}{path.stem}{color}"
                f": {color('bright magenta')}{to_address(data['address'])}{color}"
            )


@cli.command(short_help="Add a new account by entering a private key")
@click.argument("id")
def new(id):
    pk = input("Enter the private key you wish to add: ")
    a = accounts.add(pk)
    a.save(id)
    notify(
        "SUCCESS",
        f"A new account '{color('bright magenta')}{a.address}{color}'"
        f" has been generated with the id '{color('bright blue')}{id}{color}'",
    )


@cli.command(short_help="Add a new account with a random private key")
@click.argument("id")
def generate(id):
    print("Generating a new private key...")
    a = accounts.add()
    a.save(id)
    notify(
        "SUCCESS",
        f"A new account '{color('bright magenta')}{a.address}{color}'"
        f" has been generated with the id '{color('bright blue')}{id}{color}'",
    )


# Different name because `import` is a keyword
@cli.command(name="import", short_help="Import a new account via a keystore file")
@click.argument("id")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, allow_dash=True))
def _import(id, path):
    dest_path = _get_data_folder().joinpath(f"accounts/{id}.json")
    if dest_path.exists():
        raise FileExistsError(f"A keystore file already exists with the id '{id}'")

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
        f" has been imported with the id '{color('bright blue')}{id}{color}'",
    )


@cli.command(short_help="Export an existing account keystore file")
@click.argument("id")
@click.argument("path", type=click.Path(writable=True, allow_dash=True))
def export(id, path):
    source_path = _get_data_folder().joinpath(f"accounts/{id}.json")
    if not source_path.exists():
        raise FileNotFoundError(f"No keystore exists with the id '{id}'")
    dest_path = Path(path).absolute()
    if not dest_path.suffix:
        dest_path = dest_path.with_suffix(".json")
    if dest_path.exists():
        raise FileExistsError(f"Export path {dest_path} already exists")
    shutil.copy(source_path, dest_path)
    notify(
        "SUCCESS",
        f"Account with id '{color('bright blue')}{id}{color}' has been"
        f" exported to keystore '{color('bright magenta')}{dest_path}{color}'",
    )


@cli.command(short_help="Change the password of an existing account")
@click.argument("id")
def password(id):
    a = accounts.load(id)
    a.save(id, overwrite=True)
    notify("SUCCESS", f"Password has been changed for account '{color('bright blue')}{id}{color}'")


@cli.command(short_help="Delete an existing account")
@click.argument("id")
def delete(id):
    path = _get_data_folder().joinpath(f"accounts/{id}.json")
    path.unlink()
    notify("SUCCESS", f"Account '{color('bright blue')}{id}{color}' has been deleted")
