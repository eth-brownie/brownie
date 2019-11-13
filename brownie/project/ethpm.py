#!/usr/bin/python3

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from ethpm.package import resolve_uri_contents

from brownie._config import CONFIG
from brownie.convert import to_address
from brownie.exceptions import InvalidManifest
from brownie.network.web3 import web3

from . import compiler

URI_REGEX = r"""^(?:erc1319://|)([^/:\s]*)(?::[0-9]+|)/([a-z][a-z0-9_-]{0,255})@([^\s:/'";]*)$"""


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
        path = CONFIG["brownie_folder"].joinpath(
            f"data/ethpm/{address}/{package_name}/{version}.json"
        )
        try:
            with path.open("r") as fp:
                return json.load(fp)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            pass
        # TODO chain != 1
        web3._mainnet.pm.set_registry(address)
        manifest = web3._mainnet.pm.get_package(package_name, version).manifest
        manifest["registry_address"] = address

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

    for key in ("contract_types", "deployments", "sources"):
        manifest.setdefault(key, {})

    # resolve sources
    for key in list(manifest["sources"]):
        content = manifest["sources"].pop(key)
        if _is_uri(content):
            content = _get_uri_contents(content)
        # ensure all absolute imports begin with contracts/
        content = re.sub(
            r"""(import((\s*{[^};]*}\s*from)|)\s*)("|')(contracts/||/)(?=[^./])""",
            lambda k: f"{k.group(1)}{k.group(4)}contracts/",
            content,
        )
        path = Path("/").joinpath(key.lstrip("./")).resolve()
        path_str = path.as_posix()[len(path.anchor) :]
        manifest["sources"][f"contracts/{path_str}"] = content

    # set contract_name in contract_types
    contract_types = manifest["contract_types"]
    for key, value in contract_types.items():
        if "contract_name" not in value:
            value["contract_name"] = key

    # resolve package dependencies
    for dependency_uri in manifest.pop("build_dependencies", {}).values():
        dep_manifest = get_manifest(dependency_uri)
        for key in ("sources", "contract_types"):
            for k in [i for i in manifest[key] if i in dep_manifest[key]]:
                if manifest[key][k] != dep_manifest[key][k]:
                    raise InvalidManifest("Namespace collision between package dependencies")
            manifest[key].update(dep_manifest[key])

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


def get_installed_packages(project_path: Path) -> Tuple[List, List]:

    """
    Returns a list of a installed ethPM packages within a project, and a list
    of packages that are installed and one or more files are modified or deleted.

    Args:
        project_path: Path to the root folder of the project

    Returns:
        (project name, version) of installed packages
        (project name, version) of installed-but-modified packages
    """

    try:
        with project_path.joinpath("build/packages.json").open() as fp:
            packages_json = json.load(fp)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return list(), list()

    # determine if packages are installed, modified, or deleted
    installed: Set = set(packages_json["packages"])
    modified: Set = set()
    deleted: Set = set(packages_json["packages"])
    for source_path in list(packages_json["sources"]):
        package_list = packages_json["sources"][source_path]["packages"]

        # source does not exist, package has been modified
        if not project_path.joinpath(source_path).exists():
            installed.difference_update(package_list)
            modified.update(package_list)
            continue

        # source exists, package has NOT been deleted
        deleted.difference_update(package_list)
        with project_path.joinpath(source_path).open("rb") as fp:
            source = fp.read()

        if hashlib.md5(source).hexdigest() != packages_json["sources"][source_path]["md5"]:
            # package has been modified
            modified.update(package_list)

    # deleted packages have not been modified, modified packages have not been deleted
    modified.difference_update(deleted)
    installed.difference_update(modified)

    # properly remove deleted packages
    for package_name in deleted:
        remove_package(project_path, package_name, True)

    return (
        [(i, packages_json["packages"][i]["version"]) for i in sorted(installed)],
        [(i, packages_json["packages"][i]["version"]) for i in sorted(modified)],
    )


def install_package(project_path: Path, uri: str, replace_existing: bool = False) -> str:

    """
    Installs an ethPM package within the project.

    Args:
        uri: manifest URI, can be erc1319 or ipfs
        replace_existing: if True, existing files will be overwritten when
                            installing the package

    Returns: Name of the package
    """

    manifest = get_manifest(uri)
    package_name = manifest["package_name"]
    remove_package(project_path, package_name, True)
    try:
        with project_path.joinpath("build/packages.json").open() as fp:
            packages_json = json.load(fp)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        packages_json = {"sources": {}, "packages": {}}

    for path, source in manifest["sources"].items():
        source_path = project_path.joinpath(path)
        if not replace_existing and source_path.exists():
            with source_path.open() as fp:
                if fp.read() != source:
                    raise FileExistsError(
                        f"Cannot overwrite existing file with different content: '{source_path}'"
                    )

    for path, source in manifest["sources"].items():
        for folder in list(Path(path).parents)[::-1]:
            project_path.joinpath(folder).mkdir(exist_ok=True)
        with project_path.joinpath(path).open("w") as fp:
            fp.write(source)

        packages_json["sources"].setdefault(path, {"packages": []})
        packages_json["sources"][path]["md5"] = hashlib.md5(source.encode()).hexdigest()
        packages_json["sources"][path]["packages"].append(package_name)

    packages_json["packages"][package_name] = {
        "version": manifest["version"],
        "registry_address": manifest.get("registry_address", None),
    }

    with project_path.joinpath("build/packages.json").open("w") as fp:
        json.dump(packages_json, fp)
    return manifest["package_name"]


def remove_package(project_path: Path, package_name: str, delete_files: bool) -> None:

    """
    Removes an ethPM package from a project.

    Args:
        package_name: name of the package
        delete_files: if True, source files related to the package are deleted.
                      files that are still required by other installed packages
                      will not be deleted.
    """

    try:
        with project_path.joinpath("build/packages.json").open() as fp:
            packages_json = json.load(fp)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return
    for source_path in [
        k for k, v in packages_json["sources"].items() if package_name in v["packages"]
    ]:
        packages_json["sources"][source_path]["packages"].remove(package_name)
        if delete_files and not packages_json["sources"][source_path]["packages"]:
            # if source file is not associated with any other projects, delete it
            del packages_json["sources"][source_path]
            if project_path.joinpath(source_path).exists():
                project_path.joinpath(source_path).unlink()

            # remove empty folders
            for path in list(Path(source_path).parents)[:-2]:
                parent_path = project_path.joinpath(path)
                if parent_path.exists() and not list(parent_path.glob("*")):
                    parent_path.rmdir()

    if package_name in packages_json["packages"]:
        del packages_json["packages"][package_name]
    with project_path.joinpath("build/packages.json").open("w") as fp:
        json.dump(packages_json, fp)


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
