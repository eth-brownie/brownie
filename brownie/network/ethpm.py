#!/usr/bin/python3

import json
import re
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import parse_qs, urlparse

from abi2solc import generate_interface
from ethpm.package import resolve_uri_contents

from brownie._config import CONFIG
from brownie.exceptions import ContractNotFound
from brownie.project.compiler import compile_and_format

from .web3 import _resolve_address, web3

URI_REGEX = r"^(?:erc1319://|)([^/:\s]*):(?:[0-9]+)/([a-z][a-z0-9_-]{0,255})\?version=(\S*)$"
IMPORT_REGEX = r"""(?:^|;)\s*import\s*(?:{[a-zA-Z][-a-zA-Z0-9_]{0,255}}\s*from|)\s*("|')(erc1319://[^\s:/'";]*:[0-9]+/[a-z][a-z0-9_-]{0,255}@[^\s:/'";]*?)\?([^\s:/'";]*)(?=\1\s*;)"""  # NOQA: E501


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
        key = "./" + Path("/").joinpath(key.lstrip("./")).resolve().as_posix().lstrip("/")
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
        build_json = compile_and_format(manifest["sources"])
        for key, build in build_json.items():
            manifest["contract_types"].setdefault(key, {})
            manifest["contract_types"][key].update(
                {"source_path": build["sourcePath"], "abi": build["abi"]}
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


def resolve_solc_imports(contract_sources: Dict) -> Dict:
    import_sources = {}
    for path in list(contract_sources):
        for match in re.finditer(IMPORT_REGEX, contract_sources[path]):
            import_str, uri, query_str = match.group(2, 3, 4)
            query = parse_qs(query_str)
            # TODO improve these error messages
            if set(query) != {"name", "type"}:
                raise ValueError("Invalid registry URI parameters: must contain 'name' and 'type'")
            name, type_ = query["name"], query["type"]
            if type_ not in ("abi", "source"):
                raise ValueError(
                    "Invalid registry URI parameter: 'type' must be either 'abi' or 'source'"
                )

            manifest = get_manifest(uri)

            if name not in manifest["contract_types"]:
                raise ContractNotFound(f"Contract '{name}' was not found in the registry")
            if type_ == "abi":
                import_sources[import_str] = generate_interface(
                    manifest["contract_types"][name]["abi"]
                )
            else:
                source_path = manifest["contract_types"][name].get("source_path")
                if source_path is None:
                    raise ValueError(f"{name} is only available as an ABI")
                import_sources[import_str] = manifest["sources"][source_path]
                # TODO - inheritance / dependencies of this contract
    return import_sources


def _get_pm():  # type: ignore
    return web3._mainnet.pm


def _is_uri(uri: str) -> bool:
    try:
        result = urlparse(uri)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
