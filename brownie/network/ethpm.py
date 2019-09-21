#!/usr/bin/python3

import json
import re
from typing import Dict

from brownie._config import CONFIG
from brownie.exceptions import ContractNotFound

from .web3 import _resolve_address, web3

URI_REGEX = r"^(?:erc1319://|)([^/:]*):(?:[0-9]+)/([a-z][a-z0-9_-]{0,255})\?version=(\S*)$"


def get_manifest(uri: str) -> Dict:
    if not isinstance(uri, str):
        raise TypeError("EthPM manifest uri must be given as a string")
    match = re.match(URI_REGEX, uri)
    if match is None:
        raise ValueError(f"Invalid EthPM manifest uri: {uri}") from None
    address, package_name, version = match.groups()
    # TODO - chain != 1
    address = _resolve_address(address)
    path = CONFIG["brownie_folder"].joinpath("data")
    for item in ("ethpm", address, package_name):
        path = path.joinpath(item)
        path.mkdir(exist_ok=True)
    path = path.joinpath(f"{version.replace('.','-')}.json")
    try:
        with path.open("r") as fp:
            return json.load(fp)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        pm = _get_pm()
        pm.set_registry(address)
        manifest = pm.get_package(package_name, version).manifest
        # TODO if manifest doesn't include an ABI, generate one
        with path.open("w") as fp:
            json.dump(manifest, fp)
        return manifest


def get_deployed_contract_address(manifest: Dict, contract_name: str) -> str:
    for key, value in manifest.get("deployments", {}).items():
        if key.startswith(f"blockchain://{web3.genesis_hash}") and contract_name in value:
            return value[contract_name]["address"]
    raise ContractNotFound(
        f"'{manifest['package_name']}' manifest does not contain"
        f"a deployment of '{contract_name}' on this chain"
    )


def _get_pm():  # type: ignore
    return web3._mainnet.pm
