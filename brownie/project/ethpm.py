#!/usr/bin/python3

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

from ethpm.package import resolve_uri_contents

from brownie._config import CONFIG
from brownie.convert import to_address
from brownie.exceptions import InvalidManifest
from brownie.network.web3 import _resolve_address, web3

from . import compiler

URI_REGEX = (
    r"""^(?:erc1319://|)([^/:\s]*):(?:[0-9]+)/([a-z][a-z0-9_-]{0,255})@[^\s:/'";]*?/([^\s:'";]*)$"""
)


def get_manifest(uri: str) -> Dict:

    """
    Fetches an ethPM manifest and processes it for use with Brownie.
    A local copy is also stored if the given URI follows the ERC1319 spec.

    Args:
        uri: URI location of the manifest. Can be IPFS or ERC1319.
    """

    # uri can be a registry uri or a direct link to ipfs
    if not isinstance(uri, str):
        raise TypeError("EthPM manifest uri must be given as a string")

    match = re.match(URI_REGEX, uri)
    if match is None:
        # if a direct link to IPFS was used, we don't save the manifest locally
        manifest = resolve_uri_contents(uri)
        path = None
    else:
        address, package_name, version = match.groups()
        # TODO chain != 1
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

    if manifest["manifest_version"] != "2":
        raise InvalidManifest(
            f"Brownie only supports v2 ethPM manifests, this "
            f"manifest is v{manifest['manifest_version']}"
        )
    manifest = process_manifest(manifest)

    # save a local copy before returning
    if path is not None:
        with path.open("w") as fp:
            json.dump(manifest, fp)
    return manifest


def process_manifest(manifest: Dict) -> Dict:

    """
    Processes a manifest for use with Brownie.

    Args:
        manifest: ethPM manifest
    """

    for key in ("contract_types", "deployments", "sources"):
        manifest.setdefault(key, {})

    # resolve sources
    for key in list(manifest["sources"]):
        content = manifest["sources"].pop(key)
        if _is_uri(content):
            content = resolve_uri_contents(content)
        path = Path("/").joinpath(key.lstrip("./")).resolve().as_posix().lstrip("/")
        manifest["sources"][f"{manifest['package_name']}/{path}"] = content

    # resolve package dependencies
    for dependency_uri in manifest.pop("build_dependencies", {}).values():
        dependency_manifest = get_manifest(dependency_uri)
        for key in ("sources", "contract_types"):
            for k in [i for i in manifest[key] if i in dependency_manifest[key]]:
                if manifest[key][k] != dependency_manifest[key][k]:
                    raise InvalidManifest("Namespace collision between package dependencies")
            manifest[key].update(dependency_manifest.get(key, {}))

    # if manifest doesn't include an ABI, generate one
    if manifest["sources"]:
        build_json = compiler.compile_and_format(manifest["sources"])
        for key, build in build_json.items():
            manifest["contract_types"].setdefault(key, {})
            manifest["contract_types"][key].update(
                {
                    "abi": build["abi"],
                    "source_path": build["sourcePath"],
                    "all_source_paths": build["allSourcePaths"],
                }
            )
        no_source = [i for i in manifest["contract_types"].keys() if i not in build_json]
    else:
        no_source = list(manifest["contract_types"].keys())

    # delete contracts with no source or ABI, we can't do much with them
    for name in no_source:
        if "abi" not in manifest["contract_types"][name]:
            del manifest["contract_types"][name]

    # resolve or delete deployments
    for chain_uri in list(manifest["deployments"]):
        deployments = manifest["deployments"][chain_uri]
        for name in list(deployments):
            deployments[name]["address"] = to_address(deployments[name]["address"])
            alias = deployments[name]["contract_type"]
            alias = alias[alias.rfind(":") + 1 :]
            deployments[name]["contract_type"] = alias
            if alias not in manifest["contract_types"]:
                del deployments[name]
        if not deployments:
            del manifest["deployments"][chain_uri]

    manifest["brownie"] = True
    return manifest


def get_deployment_addresses(
    manifest: Dict, contract_name: str, genesis_hash: Optional[str] = None
) -> List:

    """
    Parses a manifest and returns a list of deployment addresses for the given contract
    and chain.

    Args:
        manifest: ethPM manifest
        contract_name: Name of the contract
        genesis_block: Genesis block hash for the chain to return deployments on. If
                       None, the currently active chain will be used.
    """

    if genesis_hash is None:
        genesis_hash = web3.genesis_hash

    if "brownie" not in manifest:
        manifest = process_manifest(manifest)

    chain_uri = f"blockchain://{genesis_hash}"
    key = next((i for i in manifest["deployments"] if i.startswith(chain_uri)), None)
    if key is None:
        return []
    return [
        v["address"]
        for v in manifest["deployments"][key].values()
        if manifest["contract_types"][v["contract_type"]] == contract_name
    ]


def _get_pm():  # type: ignore
    return web3._mainnet.pm


def _is_uri(uri: str) -> bool:
    try:
        result = urlparse(uri)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
