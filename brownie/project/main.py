#!/usr/bin/python3

import importlib
import json
import os
import shutil
import sys
import warnings
import zipfile
from base64 import b64encode
from hashlib import sha1
from io import BytesIO
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterator, KeysView, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

import requests
import yaml
from semantic_version import Version
from solcx.exceptions import SolcNotInstalled
from tqdm import tqdm
from vvm.exceptions import VyperNotInstalled

from brownie._config import (
    CONFIG,
    REQUEST_HEADERS,
    _get_data_folder,
    _load_project_compiler_config,
    _load_project_config,
    _load_project_dependencies,
    _load_project_structure_config,
)
from brownie.exceptions import (
    BrownieEnvironmentWarning,
    InvalidPackage,
    PragmaError,
    ProjectAlreadyLoaded,
    ProjectNotFound,
)
from brownie.network import web3
from brownie.network.contract import (
    Contract,
    ContractContainer,
    InterfaceContainer,
    ProjectContract,
)
from brownie.network.state import _add_contract, _remove_contract, _revert_register
from brownie.project import compiler, ethpm
from brownie.project.build import BUILD_KEYS, INTERFACE_KEYS, Build
from brownie.project.ethpm import get_deployment_addresses, get_manifest
from brownie.project.sources import Sources, get_pragma_spec
from brownie.utils import notify

BUILD_FOLDERS = ["contracts", "deployments", "interfaces"]
MIXES_URL = "https://github.com/brownie-mix/{}-mix/archive/master.zip"

GITIGNORE = """__pycache__
.history
.hypothesis/
build/
reports/
"""

GITATTRIBUTES = """*.sol linguist-language=Solidity
*.vy linguist-language=Python
"""

_loaded_projects = []


class _ProjectBase:

    _path: Optional[Path]
    _build_path: Optional[Path]
    _sources: Sources
    _build: Build

    def _compile(self, contract_sources: Dict, compiler_config: Dict, silent: bool) -> None:
        compiler_config.setdefault("solc", {})

        allow_paths = None
        cwd = os.getcwd()
        if self._path is not None:
            _install_dependencies(self._path)
            allow_paths = self._path.as_posix()
            os.chdir(self._path)

        try:
            build_json = compiler.compile_and_format(
                contract_sources,
                solc_version=compiler_config["solc"].get("version", None),
                vyper_version=compiler_config["vyper"].get("version", None),
                optimize=compiler_config["solc"].get("optimize", None),
                runs=compiler_config["solc"].get("runs", None),
                evm_version=compiler_config["evm_version"],
                silent=silent,
                allow_paths=allow_paths,
                remappings=compiler_config["solc"].get("remappings", []),
                optimizer=compiler_config["solc"].get("optimizer", None),
            )
        finally:
            os.chdir(cwd)

        for data in build_json.values():
            if self._build_path is not None:
                path = self._build_path.joinpath(f"contracts/{data['contractName']}.json")
                with path.open("w") as fp:
                    json.dump(data, fp, sort_keys=True, indent=2, default=sorted)
            self._build._add_contract(data)

    def _create_containers(self) -> None:
        # create container objects
        self.interface = InterfaceContainer(self)
        self._containers: Dict = {}

        for key, data in self._build.items():
            if data["type"] == "interface":
                self.interface._add(data["contractName"], data["abi"])
            if data.get("bytecode"):
                container = ContractContainer(self, data)
                self._containers[key] = container
                setattr(self, container._name, container)

    def __getitem__(self, key: str) -> ContractContainer:
        return self._containers[key]

    def __iter__(self) -> Iterator[ContractContainer]:
        return iter(self._containers[i] for i in sorted(self._containers))

    def __len__(self) -> int:
        return len(self._containers)

    def __contains__(self, item: ContractContainer) -> bool:
        return item in self._containers

    def dict(self) -> Dict:
        return dict(self._containers)

    def keys(self) -> KeysView[Any]:
        return self._containers.keys()


class Project(_ProjectBase):

    """
    Top level dict-like container that holds data and objects related to
    a brownie project.

    Attributes:
        _path: Path object, absolute path to the project
        _name: Name that the project is loaded as
        _sources: project Source object
        _build: project Build object
    """

    def __init__(self, name: str, project_path: Path) -> None:
        self._path: Path = project_path
        self._structure = _load_project_structure_config(project_path)
        self._build_path: Path = project_path.joinpath(self._structure["build"])

        self._name = name
        self._active = False
        self.load()

    def load(self) -> None:
        """Compiles the project contracts, creates ContractContainer objects and
        populates the namespace."""
        if self._active:
            raise ProjectAlreadyLoaded("Project is already active")

        contract_sources = _load_sources(self._path, self._structure["contracts"], False)
        interface_sources = _load_sources(self._path, self._structure["interfaces"], True)
        self._sources = Sources(contract_sources, interface_sources)
        self._build = Build(self._sources)

        contract_list = self._sources.get_contract_list()
        for path in list(self._build_path.glob("contracts/*.json")):
            try:
                with path.open() as fp:
                    build_json = json.load(fp)
            except json.JSONDecodeError:
                build_json = {}
            if not set(BUILD_KEYS).issubset(build_json) or path.stem not in contract_list:
                path.unlink()
                continue
            if isinstance(build_json["allSourcePaths"], list):
                # this handles the format change in v1.7.0, it can be removed in a future release
                path.unlink()
                test_path = self._build_path.joinpath("tests.json")
                if test_path.exists():
                    test_path.unlink()
                continue
            if not self._path.joinpath(build_json["sourcePath"]).exists():
                path.unlink()
                continue
            self._build._add_contract(build_json)

        interface_hashes = {}
        interface_list = self._sources.get_interface_list()
        for path in list(self._build_path.glob("interfaces/*.json")):
            try:
                with path.open() as fp:
                    build_json = json.load(fp)
            except json.JSONDecodeError:
                build_json = {}
            if not set(INTERFACE_KEYS).issubset(build_json) or path.stem not in interface_list:
                path.unlink()
                continue
            self._build._add_interface(build_json)
            interface_hashes[path.stem] = build_json["sha1"]

        self._compiler_config = _load_project_compiler_config(self._path)

        # compile updated sources, update build
        changed = self._get_changed_contracts(interface_hashes)
        self._compile(changed, self._compiler_config, False)
        self._compile_interfaces(interface_hashes)
        self._create_containers()
        self._load_deployments()

        # add project to namespaces, apply import blackmagic
        name = self._name
        self.__all__ = list(self._containers) + ["interface"]
        sys.modules[f"brownie.project.{name}"] = self  # type: ignore
        sys.modules["brownie.project"].__dict__[name] = self
        sys.modules["brownie.project"].__all__.append(name)  # type: ignore
        sys.modules["brownie.project"].__console_dir__.append(name)  # type: ignore
        self._namespaces = [
            sys.modules["__main__"].__dict__,
            sys.modules["brownie.project"].__dict__,
        ]

        # register project for revert and reset
        _revert_register(self)

        self._active = True
        _loaded_projects.append(self)

    def _get_changed_contracts(self, compiled_hashes: Dict) -> Dict:
        # get list of changed interfaces and contracts
        new_hashes = self._sources.get_interface_hashes()
        # remove outdated build artifacts
        for name in [k for k, v in new_hashes.items() if compiled_hashes.get(k, None) != v]:
            self._build._remove_interface(name)

        contracts = set(i for i in self._sources.get_contract_list() if self._compare_build_json(i))
        for contract_name in list(contracts):
            contracts.update(self._build.get_dependents(contract_name))

        # remove outdated build artifacts
        for name in contracts:
            self._build._remove_contract(name)

        # get final list of changed source paths
        changed_set: Set = set(self._sources.get_source_path(i) for i in contracts)
        return {i: self._sources.get(i) for i in changed_set}

    def _compare_build_json(self, contract_name: str) -> bool:
        config = self._compiler_config
        # confirm that this contract was previously compiled
        try:
            source = self._sources.get(contract_name)
            build_json = self._build.get(contract_name)
        except KeyError:
            return True
        # compare source hashes
        if build_json["sha1"] != sha1(source.encode()).hexdigest():
            return True
        # compare compiler settings
        if _compare_settings(config, build_json["compiler"]):
            return True
        if build_json["language"] == "Solidity":
            # compare solc-specific compiler settings
            solc_config = config["solc"].copy()
            solc_config["remappings"] = None
            if _compare_settings(solc_config, build_json["compiler"]):
                return True
            # compare solc pragma against compiled version
            if Version(build_json["compiler"]["version"]) not in get_pragma_spec(source):
                return True
        return False

    def _compile_interfaces(self, compiled_hashes: Dict) -> None:
        new_hashes = self._sources.get_interface_hashes()
        changed_paths = [
            self._sources.get_source_path(k, True)
            for k, v in new_hashes.items()
            if compiled_hashes.get(k, None) != v
        ]
        if not changed_paths:
            return

        print("Generating interface ABIs...")
        changed_sources = {i: self._sources.get(i) for i in changed_paths}
        abi_json = compiler.get_abi(
            changed_sources,
            allow_paths=self._path.as_posix(),
            remappings=self._compiler_config["solc"].get("remappings", []),
        )

        for name, abi in abi_json.items():

            with self._build_path.joinpath(f"interfaces/{name}.json").open("w") as fp:
                json.dump(abi, fp, sort_keys=True, indent=2, default=sorted)
            self._build._add_interface(abi)

    def _load_deployments(self) -> None:
        if CONFIG.network_type != "live" and not CONFIG.settings["dev_deployment_artifacts"]:
            return
        chainid = CONFIG.active_network["chainid"] if CONFIG.network_type == "live" else "dev"
        path = self._build_path.joinpath(f"deployments/{chainid}")
        path.mkdir(exist_ok=True)
        deployments = list(path.glob("*.json"))
        deployments.sort(key=lambda k: k.stat().st_mtime)
        deployment_map = self._load_deployment_map()
        for build_json in deployments:
            with build_json.open() as fp:
                build = json.load(fp)

            contract_name = build["contractName"]
            if contract_name not in self._containers:
                build_json.unlink()
                continue
            if "pcMap" in build:
                contract = ProjectContract(self, build, build_json.stem)
            else:
                contract = Contract.from_abi(  # type: ignore
                    contract_name, build_json.stem, build["abi"]
                )
                contract._project = self
            container = self._containers[contract_name]
            _add_contract(contract)
            container._contracts.append(contract)

            # update deployment map for the current chain
            instances = deployment_map.setdefault(chainid, {}).setdefault(contract_name, [])
            if build_json.stem in instances:
                instances.remove(build_json.stem)
            instances.insert(0, build_json.stem)

        self._save_deployment_map(deployment_map)

    def _load_deployment_map(self) -> Dict:
        deployment_map: Dict = {}
        map_path = self._build_path.joinpath("deployments/map.json")
        if map_path.exists():
            with map_path.open("r") as fp:
                deployment_map = json.load(fp)
        return deployment_map

    def _save_deployment_map(self, deployment_map: Dict) -> None:
        with self._build_path.joinpath("deployments/map.json").open("w") as fp:
            json.dump(deployment_map, fp, sort_keys=True, indent=2, default=sorted)

    def _remove_from_deployment_map(self, contract: ProjectContract) -> None:
        if CONFIG.network_type != "live" and not CONFIG.settings["dev_deployment_artifacts"]:
            return
        chainid = CONFIG.active_network["chainid"] if CONFIG.network_type == "live" else "dev"
        deployment_map = self._load_deployment_map()
        try:
            deployment_map[chainid][contract._name].remove(contract.address)
            if not deployment_map[chainid][contract._name]:
                del deployment_map[chainid][contract._name]
            if not deployment_map[chainid]:
                del deployment_map[chainid]
        except (KeyError, ValueError):
            pass

        self._save_deployment_map(deployment_map)

    def _add_to_deployment_map(self, contract: ProjectContract) -> None:
        if CONFIG.network_type != "live" and not CONFIG.settings["dev_deployment_artifacts"]:
            return

        chainid = CONFIG.active_network["chainid"] if CONFIG.network_type == "live" else "dev"
        deployment_map = self._load_deployment_map()
        try:
            deployment_map[chainid][contract._name].remove(contract.address)
        except (ValueError, KeyError):
            pass
        deployment_map.setdefault(chainid, {}).setdefault(contract._name, []).insert(
            0, contract.address
        )
        self._save_deployment_map(deployment_map)

    def _update_and_register(self, dict_: Any) -> None:
        dict_.update(self)
        if "interface" not in dict_:
            dict_["interface"] = self.interface
        self._namespaces.append(dict_)

    def _add_to_main_namespace(self) -> None:
        # temporarily adds project objects to the main namespace
        brownie: Any = sys.modules["brownie"]
        if "interface" not in brownie.__dict__:
            brownie.__dict__["interface"] = self.interface
        brownie.__dict__.update(self._containers)
        brownie.__all__.extend(self.__all__)

    def _remove_from_main_namespace(self) -> None:
        # removes project objects from the main namespace
        brownie: Any = sys.modules["brownie"]
        if brownie.__dict__.get("interface") == self.interface:
            del brownie.__dict__["interface"]
        for key in self._containers:
            brownie.__dict__.pop(key, None)
        for key in self.__all__:
            if key in brownie.__all__:
                brownie.__all__.remove(key)

    def __repr__(self) -> str:
        return f"<Project '{self._name}'>"

    def load_config(self) -> None:
        """Loads the project config file settings"""
        if isinstance(self._path, Path):
            _load_project_config(self._path)

    def close(self, raises: bool = True) -> None:
        """Removes pointers to the project's ContractContainer objects and this object."""
        if not self._active:
            if not raises:
                return
            raise ProjectNotFound("Project is not currently loaded.")

        # remove objects from namespace
        for dict_ in self._namespaces:
            for key in [
                k
                for k, v in dict_.items()
                if v == self or (k in self and v == self[k])  # type: ignore
            ]:
                del dict_[key]

        # remove contracts
        for contract in [x for v in self._containers.values() for x in v._contracts]:
            _remove_contract(contract)
        for container in self._containers.values():
            container._contracts.clear()
        self._containers.clear()

        # undo black-magic
        self._remove_from_main_namespace()
        name = self._name
        del sys.modules[f"brownie.project.{name}"]
        sys.modules["brownie.project"].__all__.remove(name)  # type: ignore
        sys.modules["brownie.project"].__console_dir__.remove(name)  # type: ignore
        self._active = False
        _loaded_projects.remove(self)

        # clear paths
        try:
            sys.path.remove(str(self._path))
        except ValueError:
            pass

    def _clear_dev_deployments(self, height: int) -> None:
        path = self._build_path.joinpath("deployments/dev")
        if path.exists():
            deployment_map = self._load_deployment_map()
            for deployment in path.glob("*.json"):
                if height == 0:
                    deployment.unlink()
                else:
                    with deployment.open("r") as fp:
                        deployment_artifact = json.load(fp)
                    block_height = deployment_artifact["deployment"]["blockHeight"]
                    address = deployment_artifact["deployment"]["address"]
                    contract_name = deployment_artifact["contractName"]
                    if block_height > height:
                        deployment.unlink()
                        try:
                            deployment_map["dev"][contract_name].remove(address)
                        except (KeyError, ValueError):
                            pass
            if "dev" in deployment_map and (height == 0 or not deployment_map["dev"]):
                del deployment_map["dev"]
                shutil.rmtree(path)

            self._save_deployment_map(deployment_map)

    def _revert(self, height: int) -> None:
        self._clear_dev_deployments(height)

    def _reset(self) -> None:
        self._clear_dev_deployments(0)


class TempProject(_ProjectBase):

    """Simplified Project class used to hold temporary contracts that are
    compiled via project.compile_source"""

    def __init__(self, name: str, contract_sources: Dict, compiler_config: Dict) -> None:
        self._path = None
        self._build_path = None
        self._name = name
        self._sources = Sources(contract_sources, {})
        self._build = Build(self._sources)
        self._compile(contract_sources, compiler_config, True)
        self._create_containers()

    def __repr__(self) -> str:
        return f"<TempProject '{self._name}'>"


def check_for_project(path: Union[Path, str] = ".") -> Optional[Path]:
    """Checks for a Brownie project."""
    path = Path(path).resolve()
    for folder in [path] + list(path.parents):

        structure_config = _load_project_structure_config(folder)
        contracts = folder.joinpath(structure_config["contracts"])
        interfaces = folder.joinpath(structure_config["interfaces"])
        tests = folder.joinpath(structure_config["tests"])

        if next((i for i in contracts.glob("**/*") if i.suffix in (".vy", ".sol")), None):
            return folder
        if next((i for i in interfaces.glob("**/*") if i.suffix in (".json", ".vy", ".sol")), None):
            return folder
        if contracts.is_dir() and tests.is_dir():
            return folder

    return None


def get_loaded_projects() -> List["Project"]:
    """Returns a list of currently loaded Project objects."""
    return _loaded_projects.copy()


def new(
    project_path_str: str = ".", ignore_subfolder: bool = False, ignore_existing: bool = False
) -> str:
    """Initializes a new project.

    Args:
        project_path: Path to initialize the project at. If not exists, it will be created.
        ignore_subfolder: (deprecated)
        ignore_existing: If True, will not raise when initiating in a non-empty directory.

    Returns the path to the project as a string.
    """
    project_path = Path(project_path_str).resolve()
    if not ignore_existing and project_path.exists() and list(project_path.glob("*")):
        raise FileExistsError(f"Directory is not empty: {project_path}")
    project_path.mkdir(exist_ok=True)
    _create_folders(project_path)
    _create_gitfiles(project_path)
    _add_to_sys_path(project_path)
    return str(project_path)


def from_brownie_mix(
    project_name: str, project_path: Union[Path, str] = None, ignore_subfolder: bool = False
) -> str:
    """Initializes a new project via a template. Templates are downloaded from
    https://www.github.com/brownie-mix

    Args:
        project_path: Path to initialize the project at.
        ignore_subfolders: (deprecated)

    Returns the path to the project as a string.
    """
    project_name = str(project_name).replace("-mix", "")
    url = MIXES_URL.format(project_name)
    if project_path is None:
        project_path = Path(".").joinpath(project_name)
    project_path = Path(project_path).resolve()
    if project_path.exists() and list(project_path.glob("*")):
        raise FileExistsError(f"Folder already exists - {project_path}")

    print(f"Downloading from {url}...")
    _stream_download(url, str(project_path.parent))
    project_path.parent.joinpath(project_name + "-mix-master").rename(project_path)
    _create_folders(project_path)
    _create_gitfiles(project_path)
    _add_to_sys_path(project_path)
    return str(project_path)


def from_ethpm(uri: str) -> "TempProject":

    """
    Generates a TempProject from an ethPM package.
    """

    manifest = get_manifest(uri)
    compiler_config = {
        "evm_version": None,
        "solc": {"version": None, "optimize": True, "runs": 200},
        "vyper": {"version": None},
    }
    project = TempProject(manifest["package_name"], manifest["sources"], compiler_config)
    if web3.isConnected():
        for contract_name in project.keys():
            for address in get_deployment_addresses(manifest, contract_name):
                project[contract_name].at(address)
    return project


def compile_source(
    source: str,
    solc_version: Optional[str] = None,
    vyper_version: Optional[str] = None,
    optimize: bool = True,
    runs: Optional[int] = 200,
    evm_version: Optional[str] = None,
) -> "TempProject":
    """
    Compile the given source code string and return a TempProject container with
    the ContractContainer instances.
    """
    compiler_config: Dict = {"evm_version": evm_version, "solc": {}, "vyper": {}}

    # if no compiler version was given, first try to find a Solidity pragma
    if solc_version is None and vyper_version is None:
        try:
            solc_version = compiler.solidity.find_best_solc_version(
                {"<stdin>": source}, install_needed=True, silent=False
            )
        except (PragmaError, SolcNotInstalled):
            pass

    if vyper_version is None:
        # if no vyper compiler version is given, try to compile using solidity
        compiler_config["solc"] = {
            "version": solc_version or str(compiler.solidity.get_version()),
            "optimize": optimize,
            "runs": runs,
        }
        try:
            return TempProject("TempSolcProject", {"<stdin>.sol": source}, compiler_config)
        except Exception as exc:
            # if compilation fails, raise when a solc version was given or we found a pragma
            if solc_version is not None:
                raise exc

    if vyper_version is None:
        # if no vyper compiler version was given, try to find a pragma
        try:
            vyper_version = compiler.vyper.find_best_vyper_version(
                {"<stdin>": source}, install_needed=True, silent=False
            )
        except (PragmaError, VyperNotInstalled):
            pass

    compiler_config["vyper"] = {"version": vyper_version or compiler.vyper.get_version()}
    try:
        return TempProject("TempVyperProject", {"<stdin>.vy": source}, compiler_config)
    except Exception as exc:
        if solc_version is None and vyper_version is None:
            raise PragmaError(
                "No compiler version specified, no pragma statement in the source, "
                "and compilation failed with both solc and vyper"
            ) from None
        raise exc


def load(project_path: Union[Path, str, None] = None, name: Optional[str] = None) -> "Project":
    """Loads a project and instantiates various related objects.

    Args:
        project_path: Path of the project to load. If None, will attempt to
                      locate a project using check_for_project()
        name: Name to assign to the project. If None, the name is generated
              from the name of the project folder

    Returns a Project object.
    """
    # checks
    if project_path is None:
        project_path = check_for_project(".")
        if project_path is not None and project_path != Path(".").absolute():
            warnings.warn(
                f"Loaded project has a root folder of '{project_path}' "
                "which is different from the current working directory",
                BrownieEnvironmentWarning,
            )

    elif Path(project_path).resolve() != check_for_project(project_path):
        project_path = None
    if project_path is None:
        raise ProjectNotFound("Could not find Brownie project")

    project_path = Path(project_path).resolve()
    if name is None:
        name = project_path.name
        if not name.lower().endswith("project"):
            name += " project"
        name = "".join(i for i in name.title() if i.isalpha())
    if next((True for i in _loaded_projects if i._name == name), False):
        raise ProjectAlreadyLoaded("There is already a project loaded with this name")

    # paths
    _create_folders(project_path)
    _add_to_sys_path(project_path)

    # load sources and build
    return Project(name, project_path)


def _install_dependencies(path: Path) -> None:
    for package_id in _load_project_dependencies(path):
        try:
            install_package(package_id)
        except FileExistsError:
            pass


def install_package(package_id: str) -> str:
    """
    Install a package.

    Arguments
    ---------
    package_id : str
        Package ID or ethPM URI.

    Returns
    -------
    str
        ID of the installed package.
    """
    if urlparse(package_id).scheme in ("erc1319", "ethpm"):
        return _install_from_ethpm(package_id)
    else:
        return _install_from_github(package_id)


def _install_from_ethpm(uri: str) -> str:
    manifest = get_manifest(uri)
    org = manifest["meta_brownie"]["registry_address"]
    repo = manifest["package_name"]
    version = manifest["version"]

    install_path = _get_data_folder().joinpath(f"packages/{org}")
    install_path.mkdir(exist_ok=True)
    install_path = install_path.joinpath(f"{repo}@{version}")
    if install_path.exists():
        raise FileExistsError("Package is aleady installed")

    try:
        new(str(install_path), ignore_existing=True)
        ethpm.install_package(install_path, uri)
        project = load(install_path)
        project.close()
    except Exception as e:
        shutil.rmtree(install_path)
        raise e

    return f"{org}/{repo}@{version}"


def _install_from_github(package_id: str) -> str:
    try:
        path, version = package_id.split("@")
        org, repo = path.split("/")
    except ValueError:
        raise ValueError(
            "Invalid package ID. Must be given as [ORG]/[REPO]@[VERSION]"
            "\ne.g. 'OpenZeppelin/openzeppelin-contracts@v2.5.0'"
        ) from None

    base_install_path = _get_data_folder().joinpath("packages")
    install_path = base_install_path.joinpath(f"{org}")
    install_path.mkdir(exist_ok=True)
    install_path = install_path.joinpath(f"{repo}@{version}")
    if install_path.exists():
        raise FileExistsError("Package is aleady installed")

    headers = REQUEST_HEADERS.copy()
    if os.getenv("GITHUB_TOKEN"):
        auth = b64encode(os.environ["GITHUB_TOKEN"].encode()).decode()
        headers.update({"Authorization": "Basic {}".format(auth)})

    response = requests.get(
        f"https://api.github.com/repos/{org}/{repo}/tags?per_page=100", headers=headers
    )
    if response.status_code != 200:
        msg = "Status {} when getting package versions from Github: '{}'".format(
            response.status_code, response.json()["message"]
        )
        if response.status_code == 403:
            msg += (
                "\n\nIf this issue persists, generate a Github API token and store"
                " it as the environment variable `GITHUB_TOKEN`:\n"
                "https://github.blog/2013-05-16-personal-api-tokens/"
            )
        raise ConnectionError(msg)

    data = response.json()
    if not data:
        raise ValueError("Github repository has no tags set")
    org, repo = data[0]["zipball_url"].split("/")[3:5]
    tags = [i["name"].lstrip("v") for i in data]
    if version not in tags:
        raise ValueError(
            "Invalid version for this package. Available versions are:\n" + ", ".join(tags)
        ) from None

    download_url = next(i["zipball_url"] for i in data if i["name"].lstrip("v") == version)

    existing = list(install_path.parent.iterdir())
    _stream_download(download_url, str(install_path.parent))

    installed = next(i for i in install_path.parent.iterdir() if i not in existing)
    shutil.move(installed, install_path)

    try:
        if not install_path.joinpath("brownie-config.yaml").exists():
            brownie_config: Dict = {"project_structure": {}}

            contract_paths = set(
                i.relative_to(install_path).parts[0] for i in install_path.glob("**/*.sol")
            )
            contract_paths.update(
                i.relative_to(install_path).parts[0] for i in install_path.glob("**/*.vy")
            )
            if not contract_paths:
                raise InvalidPackage(f"{package_id} does not contain any .sol or .vy files")
            if install_path.joinpath("contracts").is_dir():
                brownie_config["project_structure"]["contracts"] = "contracts"
            elif len(contract_paths) == 1:
                brownie_config["project_structure"]["contracts"] = contract_paths.pop()
            else:
                raise InvalidPackage(
                    f"{package_id} has no `contracts/` subdirectory, and "
                    "multiple directories containing source files"
                )

            with install_path.joinpath("brownie-config.yaml").open("w") as fp:
                yaml.dump(brownie_config, fp)

        project = load(install_path)
        project.close()
    except InvalidPackage:
        shutil.rmtree(install_path)
        raise
    except Exception as e:
        notify(
            "WARNING",
            f"Unable to compile {package_id} due to a {type(e).__name__} - you may still be able to"
            " import sources from the package, but will be unable to load the package directly.\n",
        )

    return f"{org}/{repo}@{version}"


def _create_gitfiles(project_path: Path) -> None:
    gitignore = project_path.joinpath(".gitignore")
    if not gitignore.exists():
        with gitignore.open("w") as fp:
            fp.write(GITIGNORE)
    gitattributes = project_path.joinpath(".gitattributes")
    if not gitattributes.exists():
        with gitattributes.open("w") as fp:
            fp.write(GITATTRIBUTES)


def _create_folders(project_path: Path) -> None:
    structure = _load_project_structure_config(project_path)
    for path in structure.values():
        project_path.joinpath(path).mkdir(exist_ok=True)
    build_path = project_path.joinpath(structure["build"])
    for path in BUILD_FOLDERS:
        build_path.joinpath(path).mkdir(exist_ok=True)


def _add_to_sys_path(project_path: Path) -> None:
    project_path_string = str(project_path)
    if project_path_string in sys.path:
        return
    sys.path.insert(0, project_path_string)


def _compare_settings(left: Dict, right: Dict) -> bool:
    return next(
        (True for k, v in left.items() if v and not isinstance(v, dict) and v != right.get(k)),
        False,
    )


def _load_sources(project_path: Path, subfolder: str, allow_json: bool) -> Dict:
    contract_sources: Dict = {}
    suffixes: Tuple = (".sol", ".vy")
    if allow_json:
        suffixes = suffixes + (".json",)

    # one day this will be a beautiful plugin system
    hooks: Optional[ModuleType] = None
    if project_path.joinpath("brownie_hooks.py").exists():
        hooks = importlib.import_module("brownie_hooks")

    for path in project_path.glob(f"{subfolder}/**/*"):
        if path.suffix not in suffixes:
            continue
        if next((i for i in path.relative_to(project_path).parts if i.startswith("_")), False):
            continue
        with path.open() as fp:
            source = fp.read()

        if hasattr(hooks, "brownie_load_source"):
            source = hooks.brownie_load_source(path, source)  # type: ignore

        path_str: str = path.relative_to(project_path).as_posix()
        contract_sources[path_str] = source
    return contract_sources


def _stream_download(download_url: str, target_path: str) -> None:
    response = requests.get(download_url, stream=True, headers=REQUEST_HEADERS)

    if response.status_code == 404:
        raise ConnectionError(
            f"404 error when attempting to download from {download_url} - "
            "are you sure this is a valid mix? https://github.com/brownie-mix"
        )
    if response.status_code != 200:
        raise ConnectionError(
            f"Received status code {response.status_code} when attempting "
            f"to download from {download_url}"
        )

    total_size = int(response.headers.get("content-length", 0))
    progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)
    content = bytes()

    for data in response.iter_content(1024, decode_unicode=True):
        progress_bar.update(len(data))
        content += data
    progress_bar.close()

    with zipfile.ZipFile(BytesIO(content)) as zf:
        zf.extractall(target_path)
