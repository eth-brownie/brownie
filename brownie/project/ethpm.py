#!/usr/bin/python3

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from abi2solc import generate_interface
from ethpm.package import resolve_uri_contents

from brownie._config import CONFIG
from brownie.network.web3 import _resolve_address, web3

from . import compiler

URI_REGEX = (
    r"""^(?:erc1319://|)([^/:\s]*):(?:[0-9]+)/([a-z][a-z0-9_-]{0,255})@[^\s:/'";]*?/([^\s:'";]*)$"""
)
IMPORT_REGEX = r"""(?:^|;)\s*import\s*(?:{[a-zA-Z][-a-zA-Z0-9_]{0,255}}\s*from|)\s*("|')((erc1319://[^\s:/'";]*:[0-9]+/[a-z][a-z0-9_-]{0,255}@[^\s:/'";]*?)/([^\s:'";]*))(?=\1\s*;)"""  # NOQA: E501


def get_manifest(uri: str) -> Dict:
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

    for key in ("contract_types", "deployments", "sources"):
        manifest.setdefault(key, {})

    # resolve sources
    for key in list(manifest["sources"]):
        content = manifest["sources"].pop(key)
        if _is_uri(content):
            content = resolve_uri_contents(content)
        key = "ethpm/" + Path("/").joinpath(key.lstrip("./")).resolve().as_posix().lstrip("/")
        manifest["sources"][key] = content

    # resolve package dependencies
    for dependency_uri in manifest.pop("build_dependencies", {}).values():
        dependency_manifest = resolve_uri_contents(dependency_uri)
        for key in ("sources", "contract_types"):
            for k in [i for i in manifest[key] if i in dependency_manifest[key]]:
                if manifest[key][k] != dependency_manifest[key][k]:
                    raise AttributeError("Namespace collision between package dependencies")
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
    for contract_name in no_source:
        if "abi" not in manifest["contract_types"][contract_name]:
            del manifest["contract_types"][contract_name]

    if path is not None:
        with path.open("w") as fp:
            json.dump(manifest, fp)
    return manifest


def get_deployed_contract_address(manifest: Dict, contract_name: str) -> Optional[str]:
    for key, value in manifest["deployments"].items():
        if key.startswith(f"blockchain://{web3.genesis_hash}") and contract_name in value:
            return value[contract_name]["address"]
    return None


def resolve_ethpm_imports(contract_sources: Dict[str, str]) -> Tuple[Dict[str, str], List]:
    ethpm_sources = {}
    remappings = {}
    for path in list(contract_sources):
        for match in re.finditer(IMPORT_REGEX, contract_sources[path]):
            import_str, uri, key_path = match.group(2, 3, 4)
            manifest = get_manifest(uri)

            type_, target = key_path.split("/", maxsplit=1)
            if type_ not in ("contract_types", "sources"):
                raise
            if type_ == "contract_types":
                if not target.endswith("/abi"):
                    raise
                contract_name = target[:-4]
                ethpm_sources[import_str] = generate_interface(
                    manifest["contract_types"][contract_name], contract_name
                )
                continue
            target = f"ethpm/{target}"
            source_paths = set(
                x
                for i in manifest["contract_types"].values()
                for x in i["all_source_paths"]
                if i["source_path"] == target
            )

            for source_path in source_paths:
                ethpm_sources[source_path] = manifest["sources"][source_path]

            remappings[import_str] = target
    return ethpm_sources, [f"{k}={v}" for k, v in remappings.items()]


def _get_pm():  # type: ignore
    return web3._mainnet.pm


def _is_uri(uri: str) -> bool:
    try:
        result = urlparse(uri)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
