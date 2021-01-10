import shutil
from pathlib import Path

import click
import yaml

from brownie._config import CONFIG, _get_data_folder
from brownie.utils import color, notify

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
    "network_id",
    "chain_id",
)


@click.group(short_help="Manage network settings")
def cli():
    """
    Settings related to local development chains and live environments.

    Each network has a unique network id. To connect to a specific network when
    running tests or launching the console, use the commandline flag `--network [network_id]`.
    """


@cli.command(short_help="List existing networks")
@click.option(
    "-v",
    "--verbose",
    default=False,
    is_flag=True,
    help="see a detailed view of available networks as well "
    "as possible data fields when declaring new networks.",
)
def list(verbose):
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


@cli.command(short_help="Add a new network", context_settings=dict(ignore_unknown_options=True))
@click.argument("environment")
@click.argument("network_id")
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def add(environment, network_id, args):
    """
    Add NETWORK_ID to ENVIRONMENT, using the settings provided in ARGS

    For example, to add a network "mainnet" to the "Ethereum" environment:

      brownie networks add Ethereum mainnet host=https://mainnet.infura.io/ chainid=1
    """
    if network_id in CONFIG.networks:
        raise ValueError(f"Network '{color('bright magenta')}{network_id}{color}' already exists")

    args = _parse_args(args)

    if "name" not in args:
        args["name"] = network_id

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    if environment.lower() == "development":
        new = {
            "name": args.pop("name"),
            "id": network_id,
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
            (i["networks"] for i in networks["live"] if i["name"].lower() == environment.lower()),
            None,
        )
        if target is None:
            networks["live"].append({"name": environment, "networks": []})
            target = networks["live"][-1]["networks"]
        new = {"id": network_id, **args}
        _validate_network(new, PROD_REQUIRED)
        target.append(new)
    with _get_data_folder().joinpath("network-config.yaml").open("w") as fp:
        yaml.dump(networks, fp)

    notify(
        "SUCCESS", f"A new network '{color('bright magenta')}{new['name']}{color}' has been added"
    )
    _print_verbose_network_description(new, True)


@cli.command(
    short_help="Modify field(s) for an existing network",
    context_settings=dict(ignore_unknown_options=True),
)
@click.argument("network_id")
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def modify(network_id, args):
    if network_id not in CONFIG.networks:
        raise ValueError(f"Network '{color('bright magenta')}{network_id}{color}' does not exist")

    args = _parse_args(args)

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    is_dev = "cmd" in CONFIG.networks[network_id]
    if is_dev:
        target = next(i for i in networks["development"] if i["id"] == network_id)
    else:
        target = next(x for i in networks["live"] for x in i["networks"] if x["id"] == network_id)

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
        target["name"] = network_id

    with _get_data_folder().joinpath("network-config.yaml").open("w") as fp:
        yaml.dump(networks, fp)

    notify(
        "SUCCESS", f"Network '{color('bright magenta')}{target['name']}{color}' has been modified"
    )
    _print_verbose_network_description(target, True)


@cli.command(short_help="Delete an existing network")
@click.argument("network_id")
def delete(network_id):
    """
    Delete NETWORK_ID from your networks
    """
    if network_id not in CONFIG.networks:
        raise ValueError(f"Network '{color('bright magenta')}{network_id}{color}' does not exist")

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    if "cmd" in CONFIG.networks[network_id]:
        networks["development"] = [i for i in networks["development"] if i["id"] != network_id]
    else:
        target = next(i for i in networks["live"] for x in i["networks"] if x["id"] == network_id)
        target["networks"] = [i for i in target["networks"] if i["id"] != network_id]
        networks["live"] = [i for i in networks["live"] if i["networks"]]

    with _get_data_folder().joinpath("network-config.yaml").open("w") as fp:
        yaml.dump(networks, fp)

    notify("SUCCESS", f"Network '{color('bright magenta')}{network_id}{color}' has been deleted")


@cli.command(name="import", short_help="Import network settings")
@click.argument("path", type=click.File("r"))
@click.option(
    "-R", "--replace", default=False, is_flag=True, help="Overwrite existing network configuration"
)
def import_(path, replace):
    """
    Load network options from PATH
    """
    new_networks = yaml.safe_load(path.read())

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        old_networks = yaml.safe_load(fp)

    for value in new_networks.get("development", []):
        network_id = value["id"]
        if network_id in CONFIG.networks:
            if "cmd" not in CONFIG.networks[network_id]:
                raise ValueError(
                    f"Import file contains development network with id '{network_id}',"
                    " but this is already an existing live network."
                )
            if not replace:
                raise ValueError(f"Cannot overwrite existing network {network_id}")
            old_networks["development"] = [
                i for i in old_networks["development"] if i["id"] != network_id
            ]
        _validate_network(value, DEV_REQUIRED)
        old_networks["development"].append(value)

    for chain, value in [(i, x) for i in new_networks.get("live", []) for x in i["networks"]]:
        prod = next((i for i in old_networks["live"] if i["name"] == chain["name"]), None)
        if prod is None:
            prod = {"name": chain["name"], "networks": []}
            old_networks["live"].append(prod)
        network_id = value["id"]
        if network_id in CONFIG.networks:
            if not replace:
                raise ValueError(f"Cannot overwrite existing network {network_id}")
            existing = next((i for i in prod["networks"] if i["id"] == network_id), None)
            if existing is None:
                raise ValueError(
                    f"Import file contains live network with id '{network_id}',"
                    " but this is already an existing network on a different environment."
                )
            prod["networks"].remove(existing)
        _validate_network(value, PROD_REQUIRED)
        prod["networks"].append(value)

    with _get_data_folder().joinpath("network-config.yaml").open("w") as fp:
        yaml.dump(old_networks, fp)

    notify(
        "SUCCESS", f"Network settings imported from '{color('bright magenta')}{path.name}{color}'"
    )


@cli.command(short_help="Export network settings")
@click.argument("path", type=click.Path(exists=False))
def export(path):
    """
    Export network settings to directory or file located at PATH

    If directory, `PATH/network-config.yaml` will be used.
    If file, PATH must be a `*.yaml` or `*.yml` file
    """
    path = Path(path)
    if path.is_dir():
        path = path.joinpath("network-config.yaml")
    elif path.suffix not in ("yaml", "yml"):
        raise ValueError(f"'{path}' must be a yaml file")

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
