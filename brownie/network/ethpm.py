#!/usr/bin/python3

import json
import re
from pathlib import Path
from typing import Dict
from urllib.parse import urlparse

from ethpm.package import resolve_uri_contents

from brownie._config import CONFIG
from brownie.exceptions import ContractNotFound

from .web3 import _resolve_address, web3

URI_REGEX = r"^(?:erc1319://|)([^/:]*):(?:[0-9]+)/([a-z][a-z0-9_-]{0,255})\?version=(\S*)$"


def get_manifest(uri: str) -> Dict:
    # uri can be a registry uri or a direct link to ipfs
    if not isinstance(uri, str):
        raise TypeError("EthPM manifest uri must be given as a string")
    match = re.match(URI_REGEX, uri)
    if match is None:
        manifest = resolve_uri_contents(uri)
        path = None
    else:
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
            pass
        pm = _get_pm()
        pm.set_registry(address)
        manifest = pm.get_package(package_name, version).manifest

    # resolve sources
    for key in list(manifest.get("sources", {})):
        content = manifest["sources"].pop(key)
        if _is_uri(content):
            content = resolve_uri_contents(content)
        key = "./" + Path("/").joinpath(key.lstrip("./")).resolve().as_posix().lstrip("/")
        manifest["sources"][key] = content

    # resolve dependencies
    for dependency_uri in manifest.pop("build_dependencies", {}).values():
        dependency_manifest = resolve_uri_contents(dependency_uri)
        for key in ("sources", "contract_types"):  # TODO deployments? link references?
            manifest.setdefault(key, {}).update(dependency_manifest.get(key, {}))

    # TODO if manifest doesn't include an ABI, generate one

    if path is not None:
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


def _is_uri(uri):
    try:
        result = urlparse(uri)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
