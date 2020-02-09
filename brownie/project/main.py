#!/usr/bin/python3

import json
import shutil
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Iterator, KeysView, List, Optional, Set, Union

import requests
from semantic_version import Version
from tqdm import tqdm

from brownie._config import (
    BROWNIE_FOLDER,
    CONFIG,
    _get_project_config_path,
    _load_project_compiler_config,
    _load_project_config,
)
from brownie.exceptions import ProjectAlreadyLoaded, ProjectNotFound
from brownie.network import web3
from brownie.network.contract import Contract, ContractContainer, ProjectContract
from brownie.network.state import _add_contract, _remove_contract
from brownie.project import compiler
from brownie.project.build import BUILD_KEYS, Build
from brownie.project.ethpm import get_deployment_addresses, get_manifest
from brownie.project.sources import Sources, get_hash, get_pragma_spec
from brownie.utils import color

FOLDERS = [
    "contracts",
    "interfaces",
    "scripts",
    "tests",
    "reports",
    "build",
    "build/contracts",
    "build/deployments",
]
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
    _sources: Sources
    _build: Build

    def _compile(self, contract_sources: Dict, compiler_config: Dict, silent: bool) -> None:
        allow_paths = None
        if self._path is not None:
            allow_paths = self._path.joinpath("contracts").as_posix()
        compiler_config.setdefault("solc", {})
        build_json = compiler.compile_and_format(
            contract_sources,
            solc_version=compiler_config["solc"].get("version", None),
            optimize=compiler_config["solc"].get("optimize", None),
            runs=compiler_config["solc"].get("runs", None),
            evm_version=compiler_config["evm_version"],
            minify=compiler_config["minify_source"],
            silent=silent,
            allow_paths=allow_paths,
            interface_sources=self._sources.get_interface_sources(),
        )
        for data in build_json.values():
            if self._path is not None:
                path = self._path.joinpath(f"build/contracts/{data['contractName']}.json")
                with path.open("w") as fp:
                    json.dump(data, fp, sort_keys=True, indent=2, default=sorted)
            self._build._add(data)

    def _create_containers(self) -> None:
        # create container objects
        self._containers: Dict = {}
        for key, data in self._build.items():
            if data["bytecode"]:
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
        self._name = name
        self._active = False
        self.load()

    def load(self) -> None:
        """Compiles the project contracts, creates ContractContainer objects and
        populates the namespace."""
        if self._active:
            raise ProjectAlreadyLoaded("Project is already active")

        contract_sources = _load_sources(self._path, "contracts", False)
        interface_sources = _load_sources(self._path, "interfaces", True)
        self._sources = Sources(contract_sources, interface_sources)
        self._build = Build(self._sources)

        contract_list = self._sources.get_contract_list()
        for path in list(self._path.glob("build/contracts/*.json")):
            try:
                with path.open() as fp:
                    build_json = json.load(fp)
            except json.JSONDecodeError:
                build_json = {}
            if not set(BUILD_KEYS).issubset(build_json) or path.stem not in contract_list:
                path.unlink()
                continue
            self._build._add(build_json)

        self._compiler_config = _load_project_compiler_config(self._path)

        # compile updated sources, update build
        changed = self._get_changed_contracts()
        self._compile(changed, self._compiler_config, False)
        self._save_interface_hashes()
        self._create_containers()
        self._load_deployments()

        # add project to namespaces, apply import blackmagic
        name = self._name
        self.__all__ = list(self._containers)
        sys.modules[f"brownie.project.{name}"] = self  # type: ignore
        sys.modules["brownie.project"].__dict__[name] = self
        sys.modules["brownie.project"].__all__.append(name)  # type: ignore
        sys.modules["brownie.project"].__console_dir__.append(name)  # type: ignore
        self._namespaces = [
            sys.modules["__main__"].__dict__,
            sys.modules["brownie.project"].__dict__,
        ]
        self._active = True
        _loaded_projects.append(self)

    def _get_changed_contracts(self) -> Dict:
        # get list of changed interfaces and contracts
        old_hashes = self._load_interface_hashes()
        new_hashes = self._sources.get_interface_hashes()
        interfaces = [k for k, v in new_hashes.items() if old_hashes.get(k, None) != v]
        contracts = [i for i in self._sources.get_contract_list() if self._compare_build_json(i)]

        # get dependents of changed sources
        final = set(contracts + interfaces)
        for contract_name in list(final):
            final.update(self._build.get_dependents(contract_name))

        # remove outdated build artifacts
        for name in [i for i in final if self._build.contains(i)]:
            self._build._remove(name)

        # get final list of changed source paths
        final.difference_update(interfaces)
        changed_set: Set = set(self._sources.get_source_path(i) for i in final)
        return {i: self._sources.get(i) for i in changed_set}

    def _load_interface_hashes(self) -> Dict:
        try:
            with self._path.joinpath("build/interfaces.json").open() as fp:
                return json.load(fp)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_interface_hashes(self) -> None:
        interface_hashes = self._sources.get_interface_hashes()
        with self._path.joinpath("build/interfaces.json").open("w") as fp:
            json.dump(interface_hashes, fp, sort_keys=True, indent=2)

    def _compare_build_json(self, contract_name: str) -> bool:
        config = self._compiler_config
        # confirm that this contract was previously compiled
        try:
            source = self._sources.get(contract_name)
            build_json = self._build.get(contract_name)
        except KeyError:
            return True
        # compare source hashes
        hash_ = get_hash(source, contract_name, config["minify_source"], build_json["language"])
        if build_json["sha1"] != hash_:
            return True
        # compare compiler settings
        if _compare_settings(config, build_json["compiler"]):
            return True
        if build_json["language"] == "Solidity":
            # compare solc-specific compiler settings
            if _compare_settings(config["solc"], build_json["compiler"]):
                return True
            # compare solc pragma against compiled version
            if Version(build_json["compiler"]["version"]) not in get_pragma_spec(source):
                return True
        return False

    def _load_deployments(self) -> None:
        if not CONFIG["active_network"].get("persist", None):
            return
        network = CONFIG["active_network"]["name"]
        path = self._path.joinpath(f"build/deployments/{network}")
        path.mkdir(exist_ok=True)
        deployments = list(
            self._path.glob(f"build/deployments/{CONFIG['active_network']['name']}/*.json")
        )
        deployments.sort(key=lambda k: k.stat().st_mtime)
        for build_json in deployments:
            with build_json.open() as fp:
                build = json.load(fp)
            if build["contractName"] not in self._containers:
                build_json.unlink()
                continue
            if "pcMap" in build:
                contract = ProjectContract(self, build, build_json.stem)
            else:
                contract = Contract(  # type: ignore
                    build["contractName"], build_json.stem, build["abi"]
                )
                contract._project = self
            container = self._containers[build["contractName"]]
            _add_contract(contract)
            container._contracts.append(contract)

    def _update_and_register(self, dict_: Any) -> None:
        dict_.update(self)
        self._namespaces.append(dict_)

    def _add_to_main_namespace(self) -> None:
        # temporarily adds project objects to the main namespace
        brownie: Any = sys.modules["brownie"]
        brownie.__dict__.update(self._containers)
        brownie.__all__.extend(self.__all__)

    def _remove_from_main_namespace(self) -> None:
        # removes project objects from the main namespace
        brownie: Any = sys.modules["brownie"]
        for key in self._containers:
            brownie.__dict__.pop(key, None)
        for key in self.__all__:
            if key in brownie.__all__:
                brownie.__all__.remove(key)

    def __repr__(self) -> str:
        return f"<Project '{color('bright magenta')}{self._name}{color}'>"

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


class TempProject(_ProjectBase):

    """Simplified Project class used to hold temporary contracts that are
    compiled via project.compile_source"""

    def __init__(self, name: str, contract_sources: Dict, compiler_config: Dict) -> None:
        self._path = None
        self._name = name
        self._sources = Sources(contract_sources, {})
        self._build = Build(self._sources)
        self._compile(contract_sources, compiler_config, True)
        self._create_containers()

    def __repr__(self) -> str:
        return f"<TempProject '{color('bright magenta')}{self._name}{color}'>"


def check_for_project(path: Union[Path, str] = ".") -> Optional[Path]:
    """Checks for a Brownie project."""
    path = Path(path).resolve()
    for folder in [path] + list(path.parents):
        if _get_project_config_path(folder):
            return folder
    return None


def get_loaded_projects() -> List:
    """Returns a list of currently loaded Project objects."""
    return _loaded_projects.copy()


def new(project_path_str: str = ".", ignore_subfolder: bool = False) -> str:
    """Initializes a new project.

    Args:
        project_path: Path to initialize the project at. If not exists, it will be created.
        ignore_subfolders: If True, will not raise if initializing in a project subfolder.

    Returns the path to the project as a string.
    """
    project_path = _new_checks(project_path_str, ignore_subfolder)
    project_path.mkdir(exist_ok=True)
    _create_folders(project_path)
    _create_gitfiles(project_path)
    if not _get_project_config_path(project_path):
        shutil.copy(
            BROWNIE_FOLDER.joinpath("data/brownie-config.yaml"),
            project_path.joinpath("brownie-config.yaml"),
        )
    if not project_path.joinpath("ethpm-config.yaml").exists():
        shutil.copy(
            BROWNIE_FOLDER.joinpath("data/ethpm-config.yaml"),
            project_path.joinpath("ethpm-config.yaml"),
        )
    _add_to_sys_path(project_path)
    return str(project_path)


def from_brownie_mix(
    project_name: str, project_path: Union[Path, str] = None, ignore_subfolder: bool = False
) -> str:
    """Initializes a new project via a template. Templates are downloaded from
    https://www.github.com/brownie-mix

    Args:
        project_path: Path to initialize the project at.
        ignore_subfolders: If True, will not raise if initializing in a project subfolder.

    Returns the path to the project as a string.
    """
    project_name = str(project_name).replace("-mix", "")
    url = MIXES_URL.format(project_name)
    if project_path is None:
        project_path = Path(".").joinpath(project_name)
    project_path = _new_checks(project_path, ignore_subfolder)
    if project_path.exists() and list(project_path.glob("*")):
        raise FileExistsError(f"Folder already exists - {project_path}")

    print(f"Downloading from {url}...")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)
    content = bytes()

    for data in response.iter_content(1024, decode_unicode=True):
        progress_bar.update(len(data))
        content += data
    progress_bar.close()

    with zipfile.ZipFile(BytesIO(content)) as zf:
        zf.extractall(str(project_path.parent))
    project_path.parent.joinpath(project_name + "-mix-master").rename(project_path)
    _create_folders(project_path)
    _create_gitfiles(project_path)
    shutil.copy(
        BROWNIE_FOLDER.joinpath("data/brownie-config.yaml"),
        project_path.joinpath("brownie-config.yaml"),
    )
    _add_to_sys_path(project_path)
    return str(project_path)


def from_ethpm(uri: str) -> "TempProject":

    """
    Generates a TempProject from an ethPM package.
    """

    manifest = get_manifest(uri)
    compiler_config = {
        "evm_version": None,
        "minify_source": False,
        "solc": {"version": None, "optimize": True, "runs": 200},
    }
    project = TempProject(manifest["package_name"], manifest["sources"], compiler_config)
    if web3.isConnected():
        for contract_name in project.keys():
            for address in get_deployment_addresses(manifest, contract_name):
                project[contract_name].at(address)
    return project


def _new_checks(project_path: Union[Path, str], ignore_subfolder: bool) -> Path:
    project_path = Path(project_path).resolve()
    if str(BROWNIE_FOLDER) in str(project_path):
        raise SystemError("Cannot make a new project inside the main brownie installation folder.")
    if not ignore_subfolder:
        check = check_for_project(project_path)
        if check and check != project_path:
            raise SystemError("Cannot make a new project in a subfolder of an existing project.")
    return project_path


def compile_source(
    source: str,
    solc_version: Optional[str] = None,
    optimize: bool = True,
    runs: Optional[int] = 200,
    evm_version: Optional[str] = None,
) -> "TempProject":
    """Compiles the given source code string and returns a TempProject container with
    the ContractContainer instances."""

    compiler_config: Dict = {"evm_version": evm_version, "minify_source": False}

    if solc_version is not None or source.lstrip().startswith("pragma"):
        compiler_config["solc"] = {"version": solc_version, "optimize": optimize, "runs": runs}
        return TempProject("TempSolcProject", {"<stdin>.sol": source}, compiler_config)

    return TempProject("TempVyperProject", {"<stdin>.vy": source}, compiler_config)


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
    if not project_path or not _get_project_config_path(Path(project_path)):
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
    for path in [i for i in FOLDERS]:
        project_path.joinpath(path).mkdir(exist_ok=True)


def _add_to_sys_path(project_path: Path) -> None:
    project_path_string = str(project_path)
    if project_path_string in sys.path:
        return
    sys.path.insert(0, project_path_string)


def _compare_settings(left: Dict, right: Dict) -> bool:
    return next(
        (True for k, v in left.items() if v and not isinstance(v, dict) and v != right[k]), False
    )


def _load_sources(project_path: Path, subfolder: str, allow_json: bool) -> Dict:
    contract_sources: Dict = {}
    for path in project_path.glob(f"{subfolder}/**/*"):
        if "/_" in path.as_posix() or path.suffix not in (".sol", ".vy", ".json"):
            continue
        with path.open() as fp:
            source = fp.read()
        path_str: str = path.relative_to(project_path).as_posix()
        contract_sources[path_str] = source
    return contract_sources
