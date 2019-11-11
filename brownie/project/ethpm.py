#!/usr/bin/python3

import hashlib
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

URI_REGEX = r"""^(?:erc1319://|)([^/:\s]*):(?:[0-9]+)/([a-z][a-z0-9_-]{0,255})@([^\s:/'";]*)$"""


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
        manifest = json.loads(_get_uri_contents(uri))
        path = None
    else:
        address, package_name, version = match.groups()
        address = _resolve_address(address)
        path = CONFIG["brownie_folder"].joinpath(
            f"data/ethpm/{address}/{package_name}/{version.replace('.','-')}.json"
        )
        try:
            with path.open("r") as fp:
                return json.load(fp)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            pass
        # TODO chain != 1
        pm = _get_pm()
        pm.set_registry(address)
        manifest = pm.get_package(package_name, version).manifest

    manifest = process_manifest(manifest)

    # save a local copy before returning
    if path is not None:
        for subfolder in list(path.parents)[2::-1]:
            subfolder.mkdir(exist_ok=True)
        with path.open("w") as fp:
            json.dump(manifest, fp)

    return manifest


def process_manifest(manifest: Dict) -> Dict:

    """
    Processes a manifest for use with Brownie.

    Args:
        manifest: ethPM manifest
    """

    if manifest["manifest_version"] != "2":
        raise InvalidManifest(
            f"Brownie only supports v2 ethPM manifests, this "
            f"manifest is v{manifest['manifest_version']}"
        )

    package_name = manifest["package_name"]
    for key in ("contract_types", "deployments", "sources"):
        manifest.setdefault(key, {})

    # resolve sources
    for key in list(manifest["sources"]):
        content = manifest["sources"].pop(key)
        if _is_uri(content):
            content = _get_uri_contents(content)
        content = _modify_absolute_imports(content, package_name)
        path = Path("/").joinpath(key.lstrip("./")).resolve()
        path_str = path.as_posix()[len(path.anchor) :]
        manifest["sources"][f"contracts/{package_name}/{path_str}"] = content

    # set contract_name in contract_types
    contract_types = manifest["contract_types"]
    for key, value in contract_types.items():
        if "contract_name" not in value:
            value["contract_name"] = key

    # resolve package dependencies
    for dependency_uri in manifest.pop("build_dependencies", {}).values():
        dep_manifest = get_manifest(dependency_uri)
        dep_name = dep_manifest["package_name"]
        manifest["contract_types"].update(
            dict((f"{dep_name}:{k}", v) for k, v in dep_manifest["contract_types"].items())
        )
        manifest["sources"].update(
            dict(
                (f"contracts/{package_name}/{k[10:]}", _modify_absolute_imports(v, package_name))
                for k, v in dep_manifest["sources"].items()
            )
        )

    # compile sources to expand contract_types
    if manifest["sources"]:
        version = compiler.find_best_solc_version(manifest["sources"], install_needed=True)

        build_json = compiler.compile_and_format(manifest["sources"], version)
        for key, build in build_json.items():
            manifest["contract_types"].setdefault(key, {"contract_name": key})
            manifest["contract_types"][key].update(
                {
                    "abi": build["abi"],
                    "source_path": build["sourcePath"],
                    "all_source_paths": build["allSourcePaths"],
                }
            )

    # delete contract_types with no source or ABI, we can't do much with them
    manifest["contract_types"] = dict(
        (k, v) for k, v in manifest["contract_types"].items() if "abi" in v
    )

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
        if manifest["contract_types"][v["contract_type"]]["contract_name"] == contract_name
    ]


def get_package_hash(package_path: Path) -> str:
    filelist = sorted(i for i in package_path.glob("**/*") if i.is_file())
    hash_ = b""
    for path in filelist:
        with path.open("rb") as fp:
            data = fp.read()
        hash_ += hashlib.md5(data).digest()
    return hashlib.md5(hash_).hexdigest()


def _get_pm():  # type: ignore
    return web3._mainnet.pm


def _is_uri(uri: str) -> bool:
    try:
        result = urlparse(uri)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def _get_uri_contents(uri: str) -> str:
    path = CONFIG["brownie_folder"].joinpath(f"data/ipfs_cache/{urlparse(uri).netloc}.ipfs")
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        data = resolve_uri_contents(uri)
        with path.open("wb") as fp:
            fp.write(data)
        return data.decode()
    with path.open() as fp:
        data = fp.read()
    return data


def _modify_absolute_imports(source: str, package_name: str) -> str:
    # adds contracts/package_name/ to start of any absolute import statements
    return re.sub(
        r"""(import((\s*{[^};]*}\s*from)|)\s*)("|')(contracts/||/)(?=[^./])""",
        lambda k: f"{k.group(1)}{k.group(4)}contracts/{package_name}/",
        source,
    )
