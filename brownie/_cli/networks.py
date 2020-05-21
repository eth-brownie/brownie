#!/usr/bin/python3

import shutil
import sys
from pathlib import Path

import yaml

from brownie._config import CONFIG, _get_data_folder
from brownie.utils import color, notify
from brownie.utils.docopt import docopt

__doc__ = """Usage: brownie networks <command> [<arguments> ...] [options]

Commands:
  list [verbose=false]             List existing networks
  add <env> <id> [key=value, ...]  Add a new network
  modify <id> [key=value, ...]     Modify field(s) for an existing network
  import <path> <replace=False>    Import network settings
  export <path>                    Export network settings
  delete <id>                      Delete an existing network

Options:
  --help -h                        Display this message

Settings related to local development chains and live environments.

Each network has a unique id. To connect to a specific network when running tests
or launching the console, use the commandline flag `--network [id]`.

To add a network you must specify an environment and id, as well as required fields.
For example, to add a network "mainnet" to the "Ethereum" environment:

  brownie networks add Ethereum mainnet host=https://mainnet.infura.io/ chainid=1

Use `brownie networks list true` to see a detailed view of available networks
as well as possible data fields when declaring new networks."""


DEV_REQUIRED = ("id", "host", "cmd", "cmd_settings")
PROD_REQUIRED = ("id", "host", "chainid")
OPTIONAL = ("name", "explorer", "timeout")

DEV_CMD_SETTINGS = (
    "port",
    "gas_limit",
    "accounts",
    "evm_version",
    "fork",
    "mnemonic",
    "account_keys_path",
    "block_time",
    "default_balance",
    "time",
)


def main():
    args = docopt(__doc__)
    try:
        fn = getattr(sys.modules[__name__], f"_{args['<command>']}")
    except AttributeError:
        print("Invalid command. Try brownie networks --help")
        return
    try:
        fn(*args["<arguments>"])
    except TypeError:
        print(f"Invalid arguments for command '{args['<command>']}'. Try brownie networks --help")
        return


def _list(verbose=False):
    if isinstance(verbose, str):
        verbose = eval(verbose.capitalize())

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    print("The following networks are declared:")

    for chain in networks["live"]:
        print(f"\n{chain['name']}")
        for value in chain["networks"]:
            is_last = value == chain["networks"][-1]
            if verbose:
                _print_verbose_network_description(value, is_last)
            else:
                _print_simple_network_description(value, is_last)

    print("\nDevelopment")
    for value in networks["development"]:
        is_last = value == networks["development"][-1]
        if verbose:
            settings = value.pop("cmd_settings")
            _print_verbose_network_description(value, value == networks["development"][-1])
            _print_verbose_network_description(settings, value == networks["development"][-1], 2)
        else:
            _print_simple_network_description(value, is_last)


def _add(env, id_, *args):
    if id_ in CONFIG.networks:
        raise ValueError(f"Network '{color('bright magenta')}{id_}{color}' already exists")

    args = _parse_args(args)

    if "name" not in args:
        args["name"] = id_

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    if env.lower() == "development":
        new = {
            "name": args.pop("name"),
            "id": id_,
            "cmd": args.pop("cmd"),
            "host": args.pop("host"),
        }
        if "timeout" in args:
            new["timeout"] = args.pop("timeout")
        new["cmd_settings"] = args
        _validate_network(new, DEV_REQUIRED)
        networks["development"].append(new)
    else:
        target = next(
            (i["networks"] for i in networks["live"] if i["name"].lower() == env.lower()), None
        )
        if target is None:
            networks["live"].append({"name": env, "networks": []})
            target = networks["live"][-1]["networks"]
        new = {"id": id_, **args}
        _validate_network(new, PROD_REQUIRED)
        target.append(new)
    with _get_data_folder().joinpath("network-config.yaml").open("w") as fp:
        yaml.dump(networks, fp)

    notify(
        "SUCCESS", f"A new network '{color('bright magenta')}{new['name']}{color}' has been added"
    )
    _print_verbose_network_description(new, True)


def _modify(id_, *args):
    if id_ not in CONFIG.networks:
        raise ValueError(f"Network '{color('bright magenta')}{id_}{color}' does not exist")

    args = _parse_args(args)

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    is_dev = "cmd" in CONFIG.networks[id_]
    if is_dev:
        target = next(i for i in networks["development"] if i["id"] == id_)
    else:
        target = next(x for i in networks["live"] for x in i["networks"] if x["id"] == id_)

    for key, value in args.items():
        t = target
        if key in DEV_CMD_SETTINGS and is_dev:
            t = target["cmd_settings"]
        if value is None:
            del t[key]
        else:
            t[key] = value
    if is_dev:
        _validate_network(target, DEV_REQUIRED)
    else:
        _validate_network(target, PROD_REQUIRED)

    if "name" not in target:
        target["name"] = id_

    with _get_data_folder().joinpath("network-config.yaml").open("w") as fp:
        yaml.dump(networks, fp)

    notify(
        "SUCCESS", f"Network '{color('bright magenta')}{target['name']}{color}' has been modified"
    )
    _print_verbose_network_description(target, True)


def _delete(id_):
    if id_ not in CONFIG.networks:
        raise ValueError(f"Network '{color('bright magenta')}{id_}{color}' does not exist")

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    if "cmd" in CONFIG.networks[id_]:
        networks["development"] = [i for i in networks["development"] if i["id"] != id_]
    else:
        target = next(i for i in networks["live"] for x in i["networks"] if x["id"] == id_)
        target["networks"] = [i for i in target["networks"] if i["id"] != id_]
        networks["live"] = [i for i in networks["live"] if i["networks"]]

    with _get_data_folder().joinpath("network-config.yaml").open("w") as fp:
        yaml.dump(networks, fp)

    notify("SUCCESS", f"Network '{color('bright magenta')}{id_}{color}' has been deleted")


def _import(path_str, replace=False):
    if isinstance(replace, str):
        replace = eval(replace.capitalize())

    path = Path(path_str)
    with path.open() as fp:
        new_networks = yaml.safe_load(fp)

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        old_networks = yaml.safe_load(fp)

    for value in new_networks.get("development", []):
        id_ = value["id"]
        if id_ in CONFIG.networks:
            if "cmd" not in CONFIG.networks[id_]:
                raise ValueError(
                    f"Import file contains development network with id '{id_}',"
                    " but this is already an existing live network."
                )
            if not replace:
                raise ValueError(f"Cannot overwrite existing network {id_}")
            old_networks["development"] = [i for i in old_networks["development"] if i["id"] != id_]
        _validate_network(value, DEV_REQUIRED)
        old_networks["development"].append(value)

    for chain, value in [(i, x) for i in new_networks.get("live", []) for x in i["networks"]]:
        prod = next((i for i in old_networks["live"] if i["name"] == chain["name"]), None)
        if prod is None:
            prod = {"name": chain["name"], "networks": []}
            old_networks["live"].append(prod)
        id_ = value["id"]
        if id_ in CONFIG.networks:
            if not replace:
                raise ValueError(f"Cannot overwrite existing network {id_}")
            existing = next((i for i in prod["networks"] if i["id"] == id_), None)
            if existing is None:
                raise ValueError(
                    f"Import file contains live network with id '{id_}',"
                    " but this is already an existing network on a different environment."
                )
            prod["networks"].remove(existing)
        _validate_network(value, PROD_REQUIRED)
        prod["networks"].append(value)

    with _get_data_folder().joinpath("network-config.yaml").open("w") as fp:
        yaml.dump(old_networks, fp)

    notify("SUCCESS", f"Network settings imported from '{color('bright magenta')}{path}{color}'")


def _export(path_str):
    path = Path(path_str)
    if path.exists():
        if path.is_dir():
            path = path.joinpath("network-config.yaml")
        else:
            raise FileExistsError(f"{path} already exists")
    if not path.suffix:
        path = path.with_suffix(".yaml")
    shutil.copy(_get_data_folder().joinpath("network-config.yaml"), path)

    notify("SUCCESS", f"Network settings exported as '{color('bright magenta')}{path}{color}'")


def _parse_args(args):
    try:
        args = dict(i.split("=") for i in args)
    except ValueError:
        raise ValueError("Arguments must be given as key=value") from None

    for key in args:
        if args[key].isdigit():
            args[key] = int(args[key])
        elif args[key].lower() in ("true", "false", "none"):
            args[key] = eval(args[key].capitalize())

    return args


def _print_simple_network_description(network_dict, is_last):
    u = "\u2514" if is_last else "\u251c"
    print(
        f"{color('bright black')}  {u}\u2500{color}{network_dict['name']}:"
        f" {color('green')}{network_dict['id']}{color}"
    )


def _print_verbose_network_description(network_dict, is_last, indent=0):
    u = "\u2514" if is_last else "\u251c"
    v = " " if is_last else "\u2502"
    if "name" in network_dict:
        print(f"{color('bright black')}  {u}\u2500{color}{network_dict.pop('name')}")

    obj_keys = sorted(network_dict)
    if "id" in obj_keys:
        obj_keys.remove("id")
        obj_keys.insert(0, "id")

    for key in obj_keys:
        value = network_dict[key]
        u = "\u2514" if key == obj_keys[-1] else "\u251c"

        if indent:
            u = (" " * indent) + u
        c = color("green") if key == "id" else ""
        print(f"{color('bright black')}  {v} {u}\u2500{color}{key}: {c}{value}{color}")


def _validate_network(network, required):
    missing = [i for i in required if i not in network]
    if missing:
        raise ValueError(f"Network is missing required field(s): {', '.join(missing)}")

    unknown = [i for i in network if i not in required + OPTIONAL]
    if unknown:
        raise ValueError(f"Unknown field(s): {', '.join(unknown)}")

    if "cmd_settings" in network:
        unknown = [i for i in network["cmd_settings"] if i not in DEV_CMD_SETTINGS]
        if unknown:
            raise ValueError(f"Unknown field(s): {', '.join(unknown)}")
