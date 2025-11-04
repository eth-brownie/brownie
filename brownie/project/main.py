#!/usr/bin/python3
# mypy: disable-error-code="union-attr"

import os
import pathlib
import shutil
import sys
import warnings
import zipfile
from base64 import b64encode
from io import BytesIO
from types import ModuleType
from typing import Any, Dict, Final, Iterator, KeysView, List, Literal, Optional, Tuple
from urllib.parse import quote

import requests
import yaml
from eth_typing import ChecksumAddress, HexStr
from mypy_extensions import mypyc_attr
from solcx.exceptions import SolcNotInstalled
from tqdm import tqdm
from ujson import JSONDecodeError
from vvm.exceptions import VyperNotInstalled

from brownie._c_constants import (
    Path,
    Version,
    import_module,
    mapcat,
    regex_match,
    sha1,
    ujson_dump,
    ujson_load,
)
from brownie._config import (
    CONFIG,
    REQUEST_HEADERS,
    _get_data_folder,
    _load_project_compiler_config,
    _load_project_config,
    _load_project_dependencies,
    _load_project_envvars,
    _load_project_structure_config,
)
from brownie._expansion import expand_posix_vars
from brownie.exceptions import (
    BadProjectName,
    BrownieEnvironmentWarning,
    InvalidPackage,
    PragmaError,
    ProjectAlreadyLoaded,
    ProjectNotFound,
)
from brownie.network.contract import (
    Contract,
    ContractContainer,
    InterfaceContainer,
    ProjectContract,
)
from brownie.network.state import _add_contract, _remove_contract, _revert_register
from brownie.project import compiler
from brownie.project.build import BUILD_KEYS, INTERFACE_KEYS, Build
from brownie.project.sources import Sources, get_pragma_spec
from brownie.typing import (
    BuildJson,
    CompilerConfig,
    ContractBuildJson,
    ContractName,
    EvmVersion,
    InterfaceBuildJson,
    Language,
    SolcConfig,
    VyperConfig,
)
from brownie.utils import notify

BUILD_FOLDERS: Final = "contracts", "deployments", "interfaces"
MIXES_URL: Final = "https://github.com/brownie-mix/{}-mix/archive/{}.zip"

GITIGNORE: Final = """__pycache__
.env
.history
.hypothesis/
build/
reports/
"""

GITATTRIBUTES: Final = """*.sol linguist-language=Solidity
*.vy linguist-language=Python
"""

NamespaceId = ContractName | Literal["interface"]
ChainDeployments = Dict[ContractName, List[ChecksumAddress]]
DeploymentMap = Dict[int | str, ChainDeployments]

_loaded_projects: Final[List["Project"]] = []


# TODO: remove this decorator once weakref support is implemented
@mypyc_attr(native_class=False)
class _ProjectBase:

    _path: Optional[pathlib.Path]
    _build_path: Optional[pathlib.Path]
    _sources: Sources
    _build: Build
    _containers: Dict[ContractName, ContractContainer]

    def _compile(
        self, contract_sources: Dict, compiler_config: CompilerConfig, silent: bool
    ) -> None:
        compiler_config.setdefault("solc", {})

        allow_paths = None
        cwd = os.getcwd()
        path = self._path
        if path is not None:
            _install_dependencies(path)
            allow_paths = path.as_posix()
            os.chdir(path)

        try:
            solc_config = compiler_config["solc"]
            vyper_config = compiler_config["vyper"]

            project_evm_version = compiler_config["evm_version"]
            evm_version: Dict[Language, Optional[EvmVersion]] = {
                "Solidity": solc_config.get("evm_version", project_evm_version),
                "Vyper": vyper_config.get("evm_version", project_evm_version),
            }

            build_json = compiler.compile_and_format(
                contract_sources,
                solc_version=solc_config.get("version", None),
                vyper_version=vyper_config.get("version", None),
                optimize=solc_config.get("optimize", None),
                runs=solc_config.get("runs", None),
                evm_version=evm_version,
                silent=silent,
                allow_paths=allow_paths,
                remappings=solc_config.get("remappings", []),
                optimizer=solc_config.get("optimizer", None),
                viaIR=solc_config.get("viaIR", None),
            )
        finally:
            os.chdir(cwd)

        build = self._build
        build_path = self._build_path
        for alias, data in build_json.items():
            if build_path is not None and not data["sourcePath"].startswith("interface"):
                # interfaces should generate artifact in /build/interfaces/ not /build/contracts/
                if alias == data["contractName"]:
                    # if the alias == contract name, this is a part of the core project
                    path = build_path.joinpath(f"contracts/{alias}.json")
                else:
                    # otherwise, this is an artifact from an external dependency
                    path = build_path.joinpath(f"contracts/dependencies/{alias}.json")
                    for parent in list(path.parents)[::-1]:
                        parent.mkdir(exist_ok=True)
                with path.open("w") as fp:
                    ujson_dump(data, fp, sort_keys=True, indent=2, default=sorted)

            if alias == data["contractName"]:
                # only add artifacts from the core project for now
                build._add_contract(data)

    def _create_containers(self) -> None:
        # create container objects
        self.interface = InterfaceContainer(self)
        self._containers = {}

        for key, data in self._build.items():
            if data["type"] == "interface":
                self.interface._add(data["contractName"], data["abi"])
            if data.get("bytecode"):
                container = ContractContainer(self, data)  # type: ignore [arg-type]
                self._containers[key] = container
                setattr(self, container._name, container)

    def __getitem__(self, key: ContractName) -> ContractContainer:
        return self._containers[key]

    def __iter__(self) -> Iterator[ContractContainer]:
        for i in sorted(self._containers):
            yield self._containers[i]

    def __len__(self) -> int:
        return len(self._containers)

    def __contains__(self, item: ContractName) -> bool:
        return item in self._containers

    def dict(self) -> Dict[ContractName, ContractContainer]:
        return dict(self._containers)

    def keys(self) -> KeysView[ContractName]:
        return self._containers.keys()


# TODO: remove this decorator once weakref support is implemented
@mypyc_attr(native_class=False)
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

    _compiler_config: CompilerConfig

    def __init__(self, name: str, project_path: pathlib.Path, compile: bool = True) -> None:
        self._path = project_path
        self._envvars: Final = _load_project_envvars(project_path)
        self._structure: Final = expand_posix_vars(
            _load_project_structure_config(project_path), self._envvars
        )
        self._build_path = project_path.joinpath(self._structure["build"])

        self._name: Final = name
        self._active: bool = False
        self.load(compile=compile)

    def load(self, raise_if_loaded: bool = True, compile: bool = True) -> None:
        """Compiles the project contracts, creates ContractContainer objects and
        populates the namespace."""
        if self._active:
            if raise_if_loaded:
                raise ProjectAlreadyLoaded("Project is already active")
            return None

        project_path: pathlib.Path = self._path  # type: ignore [assignment]
        structure = self._structure
        contract_sources = _load_sources(project_path, structure["contracts"], False)
        interface_sources = _load_sources(project_path, structure["interfaces"], True)
        sources = Sources(contract_sources, interface_sources)
        self._sources = sources

        build = Build(self._sources)
        self._build = build

        contract_list = sources.get_contract_list()
        potential_dependencies: List[Tuple[pathlib.Path, ContractBuildJson]] = []
        build_path = self._build_path

        for path in build_path.glob("contracts/*.json"):
            contract_build_json = _load_contract_build_json_from_disk(path)
            if not set(BUILD_KEYS).issubset(contract_build_json):
                path.unlink()
                continue
            if path.stem not in contract_list:
                potential_dependencies.append((path, contract_build_json))
                continue
            if isinstance(contract_build_json["allSourcePaths"], list):
                # this handles the format change in v1.7.0, it can be removed in a future release
                path.unlink()
                test_path = build_path.joinpath("tests.json")
                if test_path.exists():
                    test_path.unlink()
                continue
            if not project_path.joinpath(contract_build_json["sourcePath"]).exists():
                path.unlink()
                continue
            build._add_contract(contract_build_json)

        for path, contract_build_json in potential_dependencies:
            dependents = build.get_dependents(path.stem)  # type: ignore [arg-type]
            is_dependency = len(set(dependents) & set(contract_list)) > 0
            if is_dependency:
                build._add_contract(contract_build_json)
            else:
                path.unlink()

        interface_hashes: Dict[str, HexStr] = {}
        interface_list = sources.get_interface_list()

        for path in build_path.glob("interfaces/*.json"):
            interface_build_json = _load_interface_build_json_from_disk(path)
            if (
                not set(INTERFACE_KEYS).issubset(interface_build_json)
                or path.stem not in interface_list
            ):
                path.unlink()
                continue
            build._add_interface(interface_build_json)
            interface_hashes[path.stem] = interface_build_json["sha1"]

        if compile:
            self._compiler_config = config = expand_posix_vars(
                _load_project_compiler_config(project_path), self._envvars
            )

            # compile updated sources, update build
            changed = self._get_changed_contracts(interface_hashes)
            self._compile(changed, config, False)
            self._compile_interfaces(interface_hashes)
        self._load_dependency_artifacts()

        self._create_containers()
        self._load_deployments()

        # add project to namespaces, apply import blackmagic
        name = self._name
        self.__all__: List[NamespaceId] = list(self._containers) + ["interface"]
        sys.modules[f"brownie.project.{name}"] = self  # type: ignore [assignment]
        sys.modules["brownie.project"].__dict__[name] = self
        sys.modules["brownie.project"].__all__.append(name)
        sys.modules["brownie.project"].__console_dir__.append(name)
        self._namespaces: List[Dict[NamespaceId, ContractContainer | InterfaceContainer]] = [
            sys.modules["__main__"].__dict__,  # type: ignore [list-item]
            sys.modules["brownie.project"].__dict__,  # type: ignore [list-item]
        ]

        # register project for revert and reset
        _revert_register(self)

        self._active = True
        _loaded_projects.append(self)

    def _get_changed_contracts(self, compiled_hashes: Dict[str, HexStr]) -> Dict[str, str]:
        # get list of changed interfaces and contracts
        sources = self._sources
        new_hashes = sources.get_interface_hashes()

        # remove outdated build artifacts
        build = self._build
        for name in new_hashes:
            if compiled_hashes.get(name) != new_hashes[name]:
                build._remove_interface(name)

        contracts = {c for c in sources.get_contract_list() if self._compare_build_json(c)}
        for contract in list(contracts):
            dependents = build.get_dependents(contract)
            contracts.update(dependents)

        # remove outdated build artifacts
        for name in contracts:
            build._remove_contract(name)

        # get final list of changed source paths
        changed_set = list({sources.get_source_path(contract) for contract in contracts})
        return dict(zip(changed_set, (sources.get(changed) for changed in changed_set)))

    def _compare_build_json(self, contract_name: ContractName) -> bool:
        config = self._compiler_config
        # confirm that this contract was previously compiled
        try:
            source = self._sources.get(contract_name)
            build_json: ContractBuildJson = self._build.get(contract_name)  # type: ignore [assignment]
        except KeyError:
            return True
        # compare source hashes
        if build_json["sha1"] != sha1(source.encode()).hexdigest():
            return True
        # compare compiler settings
        compiler = build_json["compiler"]
        if build_json["language"] == "Solidity":
            # compare solc-specific compiler settings
            solc_config = config["solc"].copy()
            solc_config["remappings"] = None
            if not _solidity_compiler_equal(solc_config, compiler):
                return True
            # compare solc pragma against compiled version
            if Version(compiler["version"]) not in get_pragma_spec(source):
                return True
        else:
            if not _vyper_compiler_equal(config["vyper"], compiler):
                return True
        return False

    def _compile_interfaces(self, compiled_hashes: Dict) -> None:
        sources = self._sources
        new_hashes = sources.get_interface_hashes()
        changed_paths = [
            sources.get_source_path(k, True)
            for k, v in new_hashes.items()
            if compiled_hashes.get(k) != v
        ]
        if not changed_paths:
            return

        print("Generating interface ABIs...")
        solc_config = self._compiler_config["solc"]
        changed_sources = {i: sources.get(i) for i in changed_paths}
        abi_json = compiler.get_abi(
            changed_sources,
            solc_version=solc_config.get("version", None),
            allow_paths=self._path.as_posix(),
            remappings=solc_config.get("remappings", []),
        )

        build = self._build
        build_path = self._build_path
        for name, abi in abi_json.items():
            with build_path.joinpath(f"interfaces/{name}.json").open("w") as fp:
                ujson_dump(abi, fp, sort_keys=True, indent=2, default=sorted)
            build._add_interface(abi)

    def _load_dependency_artifacts(self) -> None:
        build = self._build
        dep_build_path = self._build_path.joinpath("contracts/dependencies/")
        for path in list(dep_build_path.glob("**/*.json")):
            contract_alias = path.relative_to(dep_build_path).with_suffix("").as_posix()
            if build.get_dependents(contract_alias):
                with path.open() as fp:
                    build_json = ujson_load(fp)
                # json.load turns arrays into python lists but for "offset" we need tuples
                build_json["offset"] = tuple(build_json["offset"])
                pc_map: Dict[Any, dict] = build_json["pcMap"]
                for counter in pc_map.values():
                    if "offset" in counter:
                        counter["offset"] = tuple(counter["offset"])
                build._add_contract(build_json, contract_alias)
            else:
                path.unlink()

    def _load_deployments(self) -> None:
        if CONFIG.network_type != "live" and not CONFIG.settings["dev_deployment_artifacts"]:
            return
        chainid = CONFIG.active_network["chainid"] if CONFIG.network_type == "live" else "dev"
        path = self._build_path.joinpath(f"deployments/{chainid}")
        path.mkdir(exist_ok=True)
        deployments = list(path.glob("*.json"))
        deployments.sort(key=lambda k: k.stat().st_mtime)
        deployment_map = self._load_deployment_map()

        build: BuildJson
        for build_json in deployments:
            with build_json.open() as fp:
                build = ujson_load(fp)

            contract_name = build["contractName"]
            if contract_name not in self._containers:
                build_json.unlink()
                continue
            if "pcMap" in build:
                contract = ProjectContract(self, build, build_json.stem)
            else:
                contract = Contract.from_abi(  # type: ignore [assignment]
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

    def _load_deployment_map(self) -> DeploymentMap:
        deployment_map = {}
        map_path = self._build_path.joinpath("deployments/map.json")
        if map_path.exists():
            with map_path.open("r") as fp:
                deployment_map = ujson_load(fp)
        return deployment_map

    def _save_deployment_map(self, deployment_map: DeploymentMap) -> None:
        with self._build_path.joinpath("deployments/map.json").open("w") as fp:
            ujson_dump(deployment_map, fp, sort_keys=True, indent=2, default=sorted)

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

    def _update_and_register(
        self,
        dict_: Dict[NamespaceId, ContractContainer | InterfaceContainer],
    ) -> None:
        dict_.update(self)  # type: ignore [arg-type]
        if "interface" not in dict_:
            dict_["interface"] = self.interface
        self._namespaces.append(dict_)

    def _add_to_main_namespace(self) -> None:
        # temporarily adds project objects to the main namespace
        brownie: ModuleType = sys.modules["brownie"]
        if "interface" not in brownie.__dict__:
            brownie.__dict__["interface"] = self.interface
        brownie.__dict__.update(self._containers)  # type: ignore [arg-type]
        brownie.__all__.extend(self.__all__)

    def _remove_from_main_namespace(self) -> None:
        # removes project objects from the main namespace
        brownie: ModuleType = sys.modules["brownie"]
        if brownie.__dict__.get("interface") == self.interface:
            del brownie.__dict__["interface"]
        for key in self._containers:
            brownie.__dict__.pop(key, None)
        for key in self.__all__:  # type: ignore [assignment]
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
            for k, v in dict_.copy().items():
                if v == self or (k in self and v == self[k]):  # type: ignore [operator, index]
                    del dict_[k]

        # remove contracts
        for container in self._containers.values():
            for contract in container._contracts:
                _remove_contract(contract)
            container._contracts.clear()
        self._containers.clear()

        # undo black-magic
        self._remove_from_main_namespace()
        name = self._name
        del sys.modules[f"brownie.project.{name}"]
        sys.modules["brownie.project"].__all__.remove(name)
        sys.modules["brownie.project"].__console_dir__.remove(name)
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
                        deployment_artifact: dict = ujson_load(fp)
                    block_height = deployment_artifact["deployment"]["blockHeight"]
                    if block_height > height:
                        deployment.unlink()
                        address = deployment_artifact["deployment"]["address"]
                        contract_name = deployment_artifact["contractName"]
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


def _load_contract_build_json_from_disk(path: pathlib.Path) -> ContractBuildJson:
    try:
        with path.open() as fp:
            contract_build_json: dict = ujson_load(fp)
            # json loads them as lists but we want tuples for mypyc
            contract_build_json["offset"] = tuple(contract_build_json["offset"])
            pc_map: dict = contract_build_json["pcMap"]
            counter: dict
            for counter in pc_map.values():
                if "offset" in counter:
                    counter["offset"] = tuple(counter["offset"])
            return contract_build_json  # type: ignore [return-value]
    except JSONDecodeError:
        return {}  # type: ignore [return-value]


def _load_interface_build_json_from_disk(path: pathlib.Path) -> InterfaceBuildJson:
    try:
        with path.open() as fp:
            interface_build_json: dict = ujson_load(fp)
            offset = interface_build_json["offset"]
            if offset is not None:
                interface_build_json["offset"] = tuple(offset)
            return interface_build_json  # type: ignore [return-value]
    except JSONDecodeError:
        return {}  # type: ignore [typeddict-item]


# TODO: remove this decorator once weakref support is implemented
@mypyc_attr(native_class=False)
class TempProject(_ProjectBase):
    """Simplified Project class used to hold temporary contracts that are
    compiled via project.compile_source"""

    def __init__(self, name: str, contract_sources: Dict, compiler_config: CompilerConfig) -> None:
        self._path = None
        self._build_path = None
        self._name: Final = name
        self._sources = Sources(contract_sources, {})
        self._build = Build(self._sources)
        self._compile(contract_sources, compiler_config, True)
        self._create_containers()

    def __repr__(self) -> str:
        return f"<TempProject '{self._name}'>"


def check_for_project(path: pathlib.Path | str = ".") -> Optional[pathlib.Path]:
    """Checks for a Brownie project."""
    path = Path(path).resolve()
    for folder in [path] + list(path.parents):

        structure_config = _load_project_structure_config(folder)
        contracts = folder.joinpath(structure_config["contracts"])
        interfaces = folder.joinpath(structure_config["interfaces"])
        scripts = folder.joinpath(structure_config["scripts"])
        tests = folder.joinpath(structure_config["tests"])

        if next((i for i in contracts.glob("**/*") if i.suffix in (".vy", ".sol")), None):
            return folder
        if next((i for i in interfaces.glob("**/*") if i.suffix in (".json", ".vy", ".sol")), None):
            return folder
        if next((i for i in scripts.glob("**/*") if i.suffix in (".py")), None):
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
    project_name: str,
    project_path: Optional[pathlib.Path | str] = None,
    ignore_subfolder: bool = False,
) -> str:
    """Initializes a new project via a template. Templates are downloaded from
    https://www.github.com/brownie-mix

    Args:
        project_path: Path to initialize the project at.
        ignore_subfolders: (deprecated)

    Returns the path to the project as a string.
    """
    project_name = str(project_name).lower().replace("-mix", "")
    headers = REQUEST_HEADERS.copy()
    headers.update(_maybe_retrieve_github_auth())
    default_branch = _get_mix_default_branch(project_name, headers)
    url = MIXES_URL.format(project_name, default_branch)
    if project_path is None:
        project_path = Path(".").joinpath(project_name)
    project_path = Path(project_path).resolve()
    if project_path.exists() and list(project_path.glob("*")):
        raise FileExistsError(f"Folder already exists - {project_path}")

    print(f"Downloading from {url}...")
    _stream_download(url, str(project_path.parent), headers)
    project_path.parent.joinpath(f"{project_name}-mix-{default_branch}").rename(project_path)
    _create_folders(project_path)
    _create_gitfiles(project_path)
    _add_to_sys_path(project_path)
    return str(project_path)


def compile_source(
    source: str,
    solc_version: Optional[str] = None,
    vyper_version: Optional[str] = None,
    optimize: bool = True,
    runs: Optional[int] = 200,
    evm_version: Optional[EvmVersion] = None,
) -> "TempProject":
    """
    Compile the given source code string and return a TempProject container with
    the ContractContainer instances.
    """
    compiler_config: CompilerConfig = {"evm_version": evm_version, "solc": {}, "vyper": {}}

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
            "version": solc_version or str(compiler.solidity.get_version().truncate()),
            "optimize": bool(optimize),
            "runs": runs or 0,
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


def load(
    project_path: Optional[pathlib.Path | str] = None,
    name: Optional[str] = None,
    raise_if_loaded: bool = True,
    compile: bool = True,
) -> "Project":
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
    else:
        project_path = Path(project_path)
        if project_path.resolve() != check_for_project(project_path):
            packages_path = _get_data_folder().joinpath("packages")
            if not project_path.is_absolute() and packages_path.joinpath(project_path).exists():
                project_path = packages_path.joinpath(project_path)
            else:
                project_path = None

    if project_path is None:
        raise ProjectNotFound("Could not find Brownie project")

    project_path = Path(project_path).resolve()
    if name is None:
        name = project_path.name
        if not name.lower().endswith("project"):
            name += " project"
        if not name[0].isalpha():
            raise BadProjectName("Project must start with an alphabetic character")
        name = "".join(i for i in name.title() if i.isalnum())

    for loaded_project in _loaded_projects:
        if loaded_project._name == name:
            if raise_if_loaded:
                raise ProjectAlreadyLoaded("There is already a project loaded with this name")
            return loaded_project

    # paths
    _create_folders(project_path)
    _add_to_sys_path(project_path)

    # load sources and build
    return Project(name, project_path, compile=compile)


def _install_dependencies(path: pathlib.Path) -> None:
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
        Package ID

    Returns
    -------
    str
        ID of the installed package.
    """
    return _install_from_github(package_id)


def _maybe_retrieve_github_auth() -> Dict[str, str]:
    """Returns appropriate github authorization headers.

    Otherwise returns an empty dict if no auth token is present.
    """
    if token := os.getenv("GITHUB_TOKEN"):
        auth = b64encode(token.encode()).decode()
        return {"Authorization": f"Basic {auth}"}
    return {}


def _install_from_github(package_id: str) -> str:
    try:
        path, version = package_id.split("@", 1)
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
        raise FileExistsError("Package is already installed")

    headers = REQUEST_HEADERS.copy()
    headers.update(_maybe_retrieve_github_auth())

    if regex_match(r"^[0-9a-f]+$", version):
        download_url = f"https://api.github.com/repos/{org}/{repo}/zipball/{version}"
    else:
        download_url = _get_download_url_from_tag(org, repo, version, headers)

    existing = list(install_path.parent.iterdir())

    # Some versions contain special characters and github api seems to display url without
    # encoding them.
    # It results in a ConnectionError exception because the actual download url is encoded.
    # In this case we try to sanitize the version in url and download again.
    try:
        _stream_download(download_url, str(install_path.parent), headers)
    except ConnectionError:
        download_url = (
            f"https://api.github.com/repos/{org}/{repo}/zipball/refs/tags/{quote(version)}"
        )
        _stream_download(download_url, str(install_path.parent), headers)

    installed = next(i for i in install_path.parent.iterdir() if i not in existing)
    shutil.move(installed, install_path)

    try:
        if not install_path.joinpath("brownie-config.yaml").exists():
            brownie_config: Dict = {"project_structure": {}}

            contract_paths = {
                i.relative_to(install_path).parts[0]
                for i in mapcat(install_path.glob, ("**/*.sol", "**/*.vy"))
            }
            if not contract_paths:
                raise InvalidPackage(f"{package_id} does not contain any .sol or .vy files")
            if install_path.joinpath("contracts").is_dir():
                brownie_config["project_structure"]["contracts"] = "contracts"
            elif len(contract_paths) == 1:
                brownie_config["project_structure"]["contracts"] = contract_paths.pop()
            else:
                raise Exception(
                    f"{package_id} has no `contracts/` subdirectory, and "
                    "multiple directories containing source files"
                )

            with install_path.joinpath("brownie-config.yaml").open("w") as fp:
                yaml.dump(brownie_config, fp)

            Path.touch(install_path / ".env")

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


def _get_download_url_from_tag(org: str, repo: str, version: str, headers: dict) -> str:
    response = requests.get(
        f"https://api.github.com/repos/{org}/{repo}/tags?per_page=100", headers=headers
    )
    status_code = response.status_code
    if status_code != 200:
        message = response.json()["message"]
        msg = f"Status {status_code} when getting package versions from Github: '{message}'"
        if status_code in {403, 404}:
            msg += (
                "\n\nMissing or forbidden.\n"
                "If this issue persists, generate a Github API token and store"
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

    return next(i["zipball_url"] for i in data if i["name"].lstrip("v") == version)


def _create_gitfiles(project_path: pathlib.Path) -> None:
    gitignore = project_path.joinpath(".gitignore")
    if not gitignore.exists():
        with gitignore.open("w") as fp:
            fp.write(GITIGNORE)
    gitattributes = project_path.joinpath(".gitattributes")
    if not gitattributes.exists():
        with gitattributes.open("w") as fp:
            fp.write(GITATTRIBUTES)


def _create_folders(project_path: pathlib.Path) -> None:
    structure = _load_project_structure_config(project_path)
    for path in structure.values():
        project_path.joinpath(path).mkdir(exist_ok=True)
    build_path = project_path.joinpath(structure["build"])
    for path in BUILD_FOLDERS:
        build_path.joinpath(path).mkdir(exist_ok=True)


def _add_to_sys_path(project_path: pathlib.Path) -> None:
    project_path_string = str(project_path)
    if project_path_string in sys.path:
        return
    sys.path.insert(0, project_path_string)


def _compare_settings(left: Dict, right: Dict) -> bool:
    return any(v and not isinstance(v, dict) and v != right.get(k) for k, v in left.items())


def _normalize_solidity_version(version: str) -> str:
    return version.split("+")[0]


def _solidity_compiler_equal(config: SolcConfig, build: CompilerConfig) -> bool:
    return (
        config["version"] is None
        or _normalize_solidity_version(config["version"])
        == _normalize_solidity_version(build["version"])
    ) and config["optimizer"] == build["optimizer"]


def _vyper_compiler_equal(config: VyperConfig, build: CompilerConfig) -> bool:
    return config["version"] is None or config["version"] == build["version"]


def _load_sources(project_path: pathlib.Path, subfolder: str, allow_json: bool) -> Dict:
    contract_sources: Dict = {}
    suffixes: Tuple = (".sol", ".vy")
    if allow_json:
        suffixes = suffixes + (".json",)

    # one day this will be a beautiful plugin system
    hooks: Optional[ModuleType] = None
    if project_path.joinpath("brownie_hooks.py").exists():
        hooks = import_module("brownie_hooks")

    for path in project_path.glob(f"{subfolder}/**/*"):
        if path.suffix not in suffixes:
            continue
        if next((i for i in path.relative_to(project_path).parts if i.startswith("_")), False):
            continue
        with path.open(encoding="utf-8") as fp:
            source = fp.read()

        if hasattr(hooks, "brownie_load_source"):
            source = hooks.brownie_load_source(path, source)

        path_str: str = path.relative_to(project_path).as_posix()
        contract_sources[path_str] = source
    return contract_sources


def _stream_download(
    download_url: str, target_path: str, headers: Dict[str, str] = REQUEST_HEADERS
) -> None:
    response = requests.get(download_url, stream=True, headers=headers)

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


def _get_mix_default_branch(mix_name: str, headers: Dict[str, str] = REQUEST_HEADERS) -> str:
    """Get the default branch for a brownie-mix repository.

    Arguments
    ---------
    mix_name : str
        Name of a brownie-mix repository without -mix appended.

    Returns
    -------
    str
        The default branch name on github.
    """
    REPO_GH_API = f"https://api.github.com/repos/brownie-mix/{mix_name}-mix"
    r = requests.get(REPO_GH_API, headers=headers)
    if r.status_code != 200:
        status, repo, message = r.status_code, f"brownie-mix/{mix_name}", r.json()["message"]
        msg = f"Status {status} when retrieving repo {repo} information from GHAPI: '{message}'"
        if r.status_code in {403, 404}:
            msg_lines = (
                msg,
                "\n\nMissing or forbidden.\n",
                "If this issue persists, generate a Github API token and store",
                " it as the environment variable `GITHUB_TOKEN`:\n",
                "https://github.blog/2013-05-16-personal-api-tokens/",
            )
            msg = "".join(msg_lines)
        raise ConnectionError(msg)
    elif "default_branch" not in r.json():
        msg = f"API results did not include {mix_name}'s default branch"
        raise KeyError(msg)

    return r.json()["default_branch"]
