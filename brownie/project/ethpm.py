#!/usr/bin/python3

import hashlib
import itertools
import json
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from ethpm._utils.ipfs import generate_file_hash
from ethpm.backends.ipfs import InfuraIPFSBackend

from brownie import network
from brownie._config import _get_data_folder
from brownie.convert import to_address
from brownie.exceptions import InvalidManifest
from brownie.network.web3 import web3
from brownie.typing import AccountsType, TransactionReceiptType
from brownie.utils import color

from . import compiler

URI_REGEX = (
    r"""^(?:erc1319://|ethpm://|)([^/:\s]*)(?::[0-9]+|)/([a-z][a-z0-9_-]{0,255})@([^\s:/'";]*)$"""
)

REGISTRY_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "packageName", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "manifestURI", "type": "string"},
        ],
        "name": "release",
        "outputs": [{"name": "releaseId", "type": "bytes32"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


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
        path = _get_data_folder().joinpath(f"ethpm/{address}/{package_name}/{version}.json")
        try:
            with path.open("r") as fp:
                return json.load(fp)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            pass
        # TODO chain != 1
        web3._mainnet.pm.set_registry(address)
        package = web3._mainnet.pm.get_package(package_name, version)
        manifest = package.manifest
        uri = package.uri

    manifest = process_manifest(manifest, uri)

    if path:
        manifest["meta_brownie"]["registry_address"] = address
        # save a local copy before returning
        for subfolder in list(path.parents)[2::-1]:
            subfolder.mkdir(exist_ok=True)
        with path.open("w") as fp:
            json.dump(manifest, fp)

    return manifest


def process_manifest(manifest: Dict, uri: Optional[str] = None) -> Dict:

    """
    Processes a manifest for use with Brownie.

    Args:
        manifest: ethPM manifest
        uri: IPFS uri of the package
    """

    if "manifest_version" not in manifest:
        raise InvalidManifest("Manifest does not specify a version")
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
        # ensure all absolute imports begin with contracts/ or interfaces/
        content = re.sub(
            r"""(import((\s*{[^};]*}\s*from)|)\s*)("|')(?!\.|contracts\/|interfaces\/)""",
            lambda k: f"{k.group(1)}{k.group(4)}contracts/",
            content,
        )
        path = Path("/").joinpath(key.lstrip("./")).resolve()
        path_str = path.as_posix()[len(path.anchor) :]
        if path.parts[1] not in ("contracts", "interfaces"):
            path_str = f"contracts/{path_str}"
        manifest["sources"][path_str] = content

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
        version: Optional[str] = None
        solc_sources = {k: v for k, v in manifest["sources"].items() if Path(k).suffix == ".sol"}
        if solc_sources:
            version = compiler.find_best_solc_version(solc_sources, install_needed=True)

        build_json = compiler.compile_and_format(
            manifest["sources"],
            solc_version=version,
            interface_sources=_get_json_interfaces(manifest["contract_types"]),
        )
        for key, build in build_json.items():
            manifest["contract_types"].setdefault(key, {"contract_name": key})
            manifest["contract_types"][key].update(
                {
                    "abi": build["abi"],
                    "source_path": build["sourcePath"],
                    "all_source_paths": sorted(build["allSourcePaths"].values()),
                    "compiler": build["compiler"],
                    "natspec": build["natspec"],
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

    manifest["meta_brownie"] = {"manifest_uri": uri, "registry_address": None}
    return manifest


def _is_uri(uri: str) -> bool:
    try:
        result = urlparse(uri)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def _get_uri_contents(uri: str) -> str:
    path = _get_data_folder().joinpath(f"ipfs_cache/{urlparse(uri).netloc}.ipfs")
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        data = InfuraIPFSBackend().fetch_uri_contents(uri)
        with path.open("wb") as fp:
            fp.write(data)
        return data.decode("utf-8")
    with path.open() as fp:
        data = fp.read()
    return data


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

    if "meta_brownie" not in manifest:
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

    packages_json = _load_packages_json(project_path)

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
        project_path: Path to the root folder of the project
        uri: manifest URI, can be erc1319, ethpm or ipfs
        replace_existing: if True, existing files will be overwritten when
                            installing the package

    Returns: Name of the package
    """

    manifest = get_manifest(uri)
    package_name = manifest["package_name"]
    remove_package(project_path, package_name, True)
    packages_json = _load_packages_json(project_path)

    # check for differences with existing source files
    if not replace_existing:
        for path, new_source in manifest["sources"].items():
            source_path = project_path.joinpath(path)
            if not source_path.exists():
                continue
            with source_path.open() as fp:
                existing_source = fp.read()
            if existing_source != new_source:
                raise FileExistsError(
                    f"Cannot overwrite existing file with different content: '{source_path}'"
                )

    # install source files
    for path, source in manifest["sources"].items():
        for folder in list(Path(path).parents)[::-1]:
            project_path.joinpath(folder).mkdir(exist_ok=True)
        with project_path.joinpath(path).open("w") as fp:
            fp.write(source)

        with project_path.joinpath(path).open("rb") as fp:
            source_bytes = fp.read()
        packages_json["sources"].setdefault(path, {"packages": []})
        packages_json["sources"][path]["md5"] = hashlib.md5(source_bytes).hexdigest()
        packages_json["sources"][path]["packages"].append(package_name)

    # install contract_types JSON interfaces
    # this relies on non-standard ethPM fields, manifests created by tooling other
    # than Brownie may not support this
    for path, abi in _get_json_interfaces(manifest["contract_types"]).items():
        with project_path.joinpath(path).open("w") as fp:
            json.dump(abi, fp, indent=2, sort_keys=True)

        with project_path.joinpath(path).open("rb") as fp:
            source_bytes = fp.read()
        packages_json["sources"].setdefault(path, {"packages": []})
        packages_json["sources"][path]["md5"] = hashlib.md5(source_bytes).hexdigest()
        packages_json["sources"][path]["packages"].append(package_name)

    # update project packages.json
    packages_json["packages"][package_name] = {
        "manifest_uri": manifest["meta_brownie"]["manifest_uri"],
        "registry_address": manifest["meta_brownie"]["registry_address"],
        "version": manifest["version"],
    }

    with project_path.joinpath("build/packages.json").open("w") as fp:
        json.dump(packages_json, fp, indent=2, sort_keys=True)
    return manifest["package_name"]


def remove_package(project_path: Path, package_name: str, delete_files: bool) -> bool:

    """
    Removes an ethPM package from a project.

    Args:
        project_path: Path to the root folder of the project
        package_name: name of the package
        delete_files: if True, source files related to the package are deleted.
                      files that are still required by other installed packages
                      will not be deleted.

    Returns: boolean indicating if package was installed.
    """

    packages_json = _load_packages_json(project_path)
    if package_name not in packages_json["packages"]:
        return False
    del packages_json["packages"][package_name]

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

    with project_path.joinpath("build/packages.json").open("w") as fp:
        json.dump(packages_json, fp, indent=2, sort_keys=True)
    return True


def create_manifest(
    project_path: Path, package_config: Dict, pin_assets: bool = False, silent: bool = True
) -> Tuple[Dict, str]:

    """
    Creates a manifest from a project, and optionally pins it to IPFS.

    Arguments:
        project_path: Path to the root folder of the project
        package_config: Configuration settings for the manifest
        pin_assets: if True, all source files and the manifest will
                    be uploaded onto IPFS via Infura.

    Returns: generated manifest, ipfs uri of manifest
    """

    package_config = _remove_empty_fields(package_config)
    _verify_package_name(package_config["package_name"])

    if pin_assets:
        ipfs_backend = InfuraIPFSBackend()

    manifest = {
        "manifest_version": "2",
        "package_name": package_config["package_name"],
        "version": package_config["version"],
        "sources": {},
        "contract_types": {},
    }
    if "meta" in package_config:
        manifest["meta"] = package_config["meta"]

    # determine base path
    if _get_path_list(project_path, "interfaces", True):
        base_path = project_path
    else:
        base_path = project_path.joinpath("contracts")

    # load packages.json and add build_dependencies
    packages_json: Dict = {"sources": {}, "packages": {}}
    if not package_config["settings"]["include_dependencies"]:
        installed, modified = get_installed_packages(project_path)
        if modified:
            raise InvalidManifest(
                f"Dependencies have been modified locally: {', '.join([i[0] for i in modified])}"
            )
        if installed:
            packages_json = _load_packages_json(project_path)
            manifest["build_dependencies"] = dict(
                (k, v["manifest_uri"]) for k, v in packages_json["packages"].items()
            )

    # add sources
    path_list = _get_path_list(project_path, "contracts", False)
    if project_path == base_path:
        path_list += _get_path_list(project_path, "interfaces", False)
    for path in path_list:
        if path.relative_to(project_path).as_posix() in packages_json["sources"]:
            continue
        if pin_assets:
            if not silent:
                print(f'Pinning "{color("bright magenta")}{path.name}{color}"...')
            uri = ipfs_backend.pin_assets(path)[0]["Hash"]
        else:
            with path.open("rb") as fp:
                uri = generate_file_hash(fp.read())
        manifest["sources"][f"./{path.relative_to(base_path).as_posix()}"] = f"ipfs://{uri}"

    # add contract_types from contracts/
    relative_to = "" if project_path == base_path else "contracts"
    for path in project_path.glob("build/contracts/*.json"):
        with path.open() as fp:
            build_json = json.load(fp)
        if build_json["sourcePath"] in packages_json["sources"]:
            # skip dependencies
            continue
        if not build_json["bytecode"] and build_json["type"] != "interface":
            # skip contracts that cannot deploy
            continue
        contract_name = build_json["contractName"]
        manifest["contract_types"][contract_name] = _get_contract_type(build_json, relative_to)

    # add contract_types from interfaces/
    for path in _get_path_list(project_path, "interfaces", True):
        if path.suffix == ".json":
            with path.open() as fp:
                data = {path.stem: json.load(fp)}
        else:
            with path.open() as fp:
                source = fp.read()
            if path.suffix == ".sol":
                data = compiler.solidity.get_abi(source)
            else:
                data = compiler.vyper.get_abi(source, path.stem)
        for name, abi in data.items():
            build_json = {
                "abi": abi,
                "contractName": name,
                "sourcePath": path.relative_to(project_path).as_posix(),
            }
            manifest["contract_types"][name] = _get_contract_type(build_json, "")

    # add deployments
    deployment_networks = package_config["settings"]["deployment_networks"]
    if deployment_networks:
        active_network = network.show_active()
        if active_network:
            network.disconnect()
        manifest["deployments"] = {}
        if isinstance(deployment_networks, str):
            deployment_networks = [deployment_networks]
        if deployment_networks == ["*"]:
            deployment_networks = [i.stem for i in project_path.glob("build/deployments/*")]
        for network_name in deployment_networks:
            instances = list(project_path.glob(f"build/deployments/{network_name}/*.json"))
            if not instances:
                continue
            instances.sort(key=lambda k: k.stat().st_mtime, reverse=True)
            network.connect(network_name)
            manifest["deployments"][web3.chain_uri] = {}
            for path in instances:
                with path.open() as fp:
                    build_json = json.load(fp)

                alias = build_json["contractName"]
                source_path = build_json["sourcePath"]
                if source_path in packages_json["sources"]:
                    alias = f"{packages_json['sources'][source_path]['packages'][0]}:{alias}"

                if alias in manifest["contract_types"]:
                    # skip deployment if bytecode does not match that of contract_type
                    bytecode = manifest["contract_types"][alias]["deployment_bytecode"]["bytecode"]
                    if f"0x{build_json['bytecode']}" != bytecode:
                        continue
                else:
                    # add contract_type for dependency
                    manifest["contract_types"][alias] = _get_contract_type(build_json, relative_to)

                key = build_json["contractName"]
                for i in itertools.count(1):
                    if key not in manifest["deployments"][web3.chain_uri]:
                        break
                    key = f"{build_json['contractName']}-{i}"

                manifest["deployments"][web3.chain_uri][key] = {
                    "address": path.stem,
                    "contract_type": alias,
                }
            network.disconnect()
        if active_network:
            network.connect(active_network)
        if not manifest["deployments"]:
            del manifest["deployments"]

    uri = None
    if pin_assets:
        if not silent:
            print("Pinning manifest...")
        temp_path = Path(tempfile.gettempdir()).joinpath("manifest.json")
        with temp_path.open("w") as fp:
            json.dump(manifest, fp, sort_keys=True, separators=(",", ":"))
        uri = ipfs_backend.pin_assets(temp_path)[0]["Hash"]

    return manifest, uri


def verify_manifest(package_name: str, version: str, uri: str) -> None:

    """
    Verifies the validity of a package at a given IPFS URI.

    Arguments:
        package_name: Package name
        version: Package version
        uri: IPFS uri

    Returns None if the package is valid, raises InvalidManifest if not.
    """

    _verify_package_name(package_name)
    data = InfuraIPFSBackend().fetch_uri_contents(uri).decode("utf-8")
    try:
        manifest = json.loads(data)
    except Exception:
        raise InvalidManifest("URI did not return valid JSON encoded data")
    if json.dumps(manifest, sort_keys=True, separators=(",", ":")) != data:
        raise InvalidManifest("JSON data is not tightly packed with sorted keys")
    for key, value in [
        ("manifest_version", "2"),
        ("package_name", package_name),
        ("version", version),
    ]:
        if manifest.get(key, None) != value:
            raise InvalidManifest(f"Missing or invalid field: {key}")
    try:
        process_manifest(manifest)
    except Exception as e:
        raise InvalidManifest(f"Cannot process manifest - {str(e)}")


def release_package(
    registry_address: str, account: AccountsType, package_name: str, version: str, uri: str
) -> TransactionReceiptType:

    """
    Creates a new release of a package at an ERC1319 registry.

    Arguments:
        registry_address: Address of the registry
        account: Account object used to broadcast the transaction to the registry
        package_name: Name of the package
        version: Package version
        uri: IPFS uri of the package
    """

    registry = network.contract.Contract.from_abi(
        "ERC1319Registry", registry_address, REGISTRY_ABI, owner=account
    )
    verify_manifest(package_name, version, uri)
    return registry.release(package_name, version, uri)


def _get_contract_type(build_json: Dict, relative_to: str) -> Dict:
    contract_type = {
        "abi": build_json["abi"],
        "contract_name": build_json["contractName"],
        "source_path": f"./{Path(build_json['sourcePath']).relative_to(relative_to)}",
    }
    if build_json.get("bytecode", None):
        contract_type.update(
            compiler={
                "name": "solc" if build_json["language"] == "Solidity" else "vyper",
                "version": build_json["compiler"]["version"],
                "settings": {"evmVersion": build_json["compiler"]["evm_version"]},
            },
            deployment_bytecode={"bytecode": f"0x{build_json['bytecode']}"},
            runtime_bytecode={"bytecode": f"0x{build_json['deployedBytecode']}"},
        )
        if build_json["language"] == "Solidity":
            contract_type["compiler"]["settings"]["optimizer"] = build_json["compiler"].get(
                "optimizer", {}
            )
    return contract_type


def _load_packages_json(project_path: Path) -> Dict:
    try:
        with project_path.joinpath("build/packages.json").open() as fp:
            return json.load(fp)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {"sources": {}, "packages": {}}


def _remove_empty_fields(initial: Dict) -> Dict:
    result = {}
    for key, value in initial.items():
        if isinstance(initial[key], dict):
            value = _remove_empty_fields(value)
        if isinstance(initial[key], list):
            value = [i for i in initial[key] if i is not None]
        if value not in (None, {}, [], ""):
            result[key] = value
    return result


def _verify_package_name(package_name: str) -> None:
    if re.fullmatch(r"^[a-z][a-z0-9_-]{0,255}$", package_name) is None:
        raise ValueError(f"Invalid package name '{package_name}'")


def _get_path_list(project_path: Path, subfolder: str, allow_json: bool) -> List:
    path_iter = project_path.glob(f"{subfolder}/**/*")
    suffixes: Tuple = (".sol", ".vy")
    if allow_json:
        suffixes += (".json",)
    return [i for i in path_iter if "/_" not in i.as_posix() and i.suffix in suffixes]


def _get_json_interfaces(contract_types: Dict) -> Dict:
    interfaces = {}
    for data in contract_types.values():
        if "source_path" not in data or "abi" not in data:
            continue
        path = Path(data["source_path"])
        if path.parts[0] != "interfaces" or path.suffix != ".json":
            continue
        interfaces[data["source_path"]] = data["abi"]
    return interfaces
