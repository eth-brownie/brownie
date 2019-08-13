#!/usr/bin/python3

from io import BytesIO
from pathlib import Path
import requests
import shutil
import sys
import zipfile

from brownie.cli.utils import color
from brownie.network.contract import ContractContainer
from brownie.exceptions import (
    ProjectAlreadyLoaded,
    ProjectNotFound,
)
from brownie.project import compiler
from brownie.project.sources import Sources, get_hash
from brownie.project.build import Build
from brownie._config import CONFIG, load_project_config, load_project_compiler_config

FOLDERS = [
    "contracts",
    "scripts",
    "reports",
    "tests",
    "build",
    "build/contracts",
    "build/tests"
]
MIXES_URL = "https://github.com/brownie-mix/{}-mix/archive/master.zip"

_loaded_projects = []


class _ProjectBase:

    def __init__(self, project_path, name):
        self._project_path = project_path
        self._name = name
        self._sources = Sources(project_path)
        self._build = Build(project_path, self._sources)

    def _compile(self, sources, compiler_config, silent):
        build_json = compiler.compile_and_format(
            sources,
            solc_version=compiler_config['version'],
            optimize=compiler_config['optimize'],
            runs=compiler_config['runs'],
            evm_version=compiler_config['evm_version'],
            minify=compiler_config['minify_source'],
            silent=silent
        )
        for data in build_json.values():
            self._build.add(data)

    def _create_containers(self):
        # create container objects
        self._containers = {}
        for key, data in self._build.items():
            if data['bytecode']:
                container = ContractContainer(self, data)
                self._containers[key] = container
                setattr(self, container._name, container)

    def __getitem__(self, key):
        return self._containers[key]

    def __iter__(self):
        return iter(self._containers[i] for i in sorted(self._containers))

    def __len__(self):
        return len(self._containers)

    def __contains__(self, item):
        return item in self._containers

    def dict(self):
        return dict(self._containers)

    def keys(self):
        return self._containers.keys()


class Project(_ProjectBase):

    '''
    Top level dict-like container that holds data and objects related to
    a brownie project.

    Attributes:
        _project_path: Path object, absolute path to the project
        _name: Name that the project is loaded as
        _sources: project Source object
        _build: project Build object
    '''

    def __init__(self, project_path, name):
        super().__init__(project_path, name)
        self._active = False
        self.load()

    def load(self):
        '''Compiles the project contracts, creates ContractContainer objects and
        populates the namespace.'''
        if self._active:
            raise ProjectAlreadyLoaded("Project is already active")

        self._compiler_config = load_project_compiler_config(self._project_path)
        solc_version = self._compiler_config['version']
        if solc_version:
            self._compiler_config['version'] = compiler.set_solc_version(solc_version)

        # compile updated sources, update build
        changed = self._get_changed_contracts()
        self._compiler_config['version'] = solc_version
        self._compile(changed, self._compiler_config, False)
        self._create_containers()

        # add project to namespaces, apply import blackmagic
        name = self._name
        self.__all__ = list(self._containers)
        sys.modules[f'brownie.project.{name}'] = self
        sys.modules['brownie.project'].__dict__[name] = self
        sys.modules['brownie.project'].__all__.append(name)
        sys.modules['brownie.project'].__console_dir__.append(name)
        self._namespaces = [
            sys.modules['__main__'].__dict__,
            sys.modules['brownie.project'].__dict__
        ]
        self._active = True
        _loaded_projects.append(self)

    def _get_changed_contracts(self):
        changed = [i for i in self._sources.get_contract_list() if self._compare_build_json(i)]
        final = set(changed)
        for contract_name in changed:
            final.update(self._build.get_dependents(contract_name))
        for name in [i for i in final if self._build.contains(i)]:
            self._build.delete(name)
        changed = set(self._sources.get_source_path(i) for i in final)
        return dict((i, self._sources.get(i)) for i in changed)

    def _compare_build_json(self, contract_name):
        config = self._compiler_config
        try:
            source = self._sources.get(contract_name)
            build_json = self._build.get(contract_name)
        except KeyError:
            return True
        if build_json['sha1'] != get_hash(source, contract_name, config['minify_source']):
            return True
        return next(
            (True for k, v in build_json['compiler'].items() if config[k] and v != config[k]),
            False
        )

    def _update_and_register(self, dict_):
        dict_.update(self)
        self._namespaces.append(dict_)

    def __repr__(self):
        return f"<Project object '{color['string']}{self._name}{color}'>"

    def load_config(self):
        '''Loads the project config file settings'''
        load_project_config(self._project_path)

    def close(self, raises=True):
        '''Removes pointers to the project's ContractContainer objects and this object.'''
        if not self._active:
            if not raises:
                return
            raise ProjectNotFound("Project is not currently loaded.")

        # remove objects from namespace
        for dict_ in self._namespaces:
            for key in [k for k, v in dict_.items() if v == self or (k in self and v == self[k])]:
                del dict_[key]

        name = self._name
        del sys.modules[f'brownie.project.{name}']
        sys.modules['brownie.project'].__all__.remove(name)
        sys.modules['brownie.project'].__console_dir__.remove(name)
        self._active = False
        _loaded_projects.remove(self)

        # clear paths
        try:
            sys.path.remove(self._project_path)
        except ValueError:
            pass


class TempProject(_ProjectBase):

    '''Simplified Project class used to hold temporary contracts that are
    compiled via project.compile_source'''

    def __init__(self, source, compiler_config):
        super().__init__(None, "TempProject")
        self._sources.add("<stdin>", source)
        self._compile({'<stdin>': source}, compiler_config, True)
        self._create_containers()

    def __repr__(self):
        return f"<TempProject object>"


def check_for_project(path="."):
    '''Checks for a Brownie project.'''
    path = Path(path).resolve()
    for folder in [path] + list(path.parents):
        if folder.joinpath("brownie-config.json").exists():
            return folder
    return None


def get_loaded_projects():
    '''Returns a list of currently loaded Project objects.'''
    return _loaded_projects.copy()


def new(project_path=".", ignore_subfolder=False):
    '''Initializes a new project.

    Args:
        project_path: Path to initialize the project at. If not exists, it will be created.
        ignore_subfolders: If True, will not raise if initializing in a project subfolder.

    Returns the path to the project as a string.
    '''
    project_path = _new_checks(project_path, ignore_subfolder)
    project_path.mkdir(exist_ok=True)
    _create_folders(project_path)
    if not project_path.joinpath('brownie-config.json').exists():
        shutil.copy(
            str(Path(CONFIG['folders']['brownie']).joinpath("data/config.json")),
            str(project_path.joinpath('brownie-config.json'))
        )
    _add_to_sys_path(project_path)
    return str(project_path)


def pull(project_name, project_path=None, ignore_subfolder=False):
    '''Initializes a new project via a template. Templates are downloaded from
    https://www.github.com/brownie-mix

    Args:
        project_path: Path to initialize the project at.
        ignore_subfolders: If True, will not raise if initializing in a project subfolder.

    Returns the path to the project as a string.
    '''
    project_name = str(project_name).replace('-mix', '')
    url = MIXES_URL.format(project_name)
    if project_path is None:
        project_path = Path('.').joinpath(project_name)
    project_path = _new_checks(project_path, ignore_subfolder)
    if project_path.exists():
        raise FileExistsError(f"Folder already exists - {project_path}")

    print(f"Downloading from {url}...")
    request = requests.get(url)
    with zipfile.ZipFile(BytesIO(request.content)) as zf:
        zf.extractall(str(project_path.parent))
    project_path.parent.joinpath(project_name + '-mix-master').rename(project_path)
    shutil.copy(
        str(Path(CONFIG['folders']['brownie']).joinpath("data/config.json")),
        str(project_path.joinpath('brownie-config.json'))
    )
    _add_to_sys_path(project_path)
    return str(project_path)


def _new_checks(project_path, ignore_subfolder):
    project_path = Path(project_path).resolve()
    if CONFIG['folders']['brownie'] in str(project_path):
        raise SystemError("Cannot make a new project inside the main brownie installation folder.")
    if not ignore_subfolder:
        check = check_for_project(project_path)
        if check and check != project_path:
            raise SystemError("Cannot make a new project in a subfolder of an existing project.")
    return project_path


def compile_source(source, solc_version=None, optimize=True, runs=200, evm_version=None):
    '''Compiles the given source code string and returns a TempProject container with
    the ContractContainer instances.'''

    compiler_config = {
        'version': solc_version,
        'optimize': optimize,
        'runs': runs,
        'evm_version': evm_version,
        'minify_source': False
    }
    return TempProject(source, compiler_config)


def load(project_path=None, name=None):
    '''Loads a project and instantiates various related objects.

    Args:
        project_path: Path of the project to load. If None, will attempt to
                      locate a project using check_for_project()

    Returns a list of ContractContainer objects.
    '''
    # checks
    if project_path is None:
        project_path = check_for_project('.')
    if not project_path or not Path(project_path).joinpath("brownie-config.json").exists():
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
    return Project(project_path, name)


def _create_folders(project_path):
    for path in [i for i in FOLDERS]:
        project_path.joinpath(path).mkdir(exist_ok=True)


def _add_to_sys_path(project_path):
    project_path = str(project_path)
    if project_path in sys.path:
        return
    sys.path.insert(0, project_path)
