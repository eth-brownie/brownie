#!/usr/bin/python3

from io import BytesIO
from pathlib import Path
import requests
import shutil
import sys
import zipfile

from brownie.cli.utils import color
from brownie.network.contract import ContractContainer
from brownie.exceptions import ProjectAlreadyLoaded, ProjectNotFound
from brownie.project import compiler
from brownie.project.sources import Sources, get_hash
from brownie.project.build import Build
# from brownie.test import coverage
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


def check_for_project(path):
    '''Checks for a Brownie project.'''
    path = Path(path).resolve()
    for folder in [path]+list(path.parents):
        if folder.joinpath("brownie-config.json").exists():
            return folder
    return None


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
    project_path.parent.joinpath(project_name+'-mix-master').rename(project_path)
    shutil.copy(
        str(Path(CONFIG['folders']['brownie']).joinpath("data/config.json")),
        str(project_path.joinpath('brownie-config.json'))
    )
    _add_to_sys_path(project_path)
    return str(project_path)


def _new_checks(project_path, ignore_subfolder):
    if CONFIG['folders']['project']:
        raise ProjectAlreadyLoaded("Project has already been loaded")
    project_path = Path(project_path).resolve()
    if CONFIG['folders']['brownie'] in str(project_path):
        raise SystemError("Cannot make a new project inside the main brownie installation folder.")
    if not ignore_subfolder:
        check = check_for_project(project_path)
        if check and check != project_path:
            raise SystemError("Cannot make a new project in a subfolder of an existing project.")
    return project_path


# def close(raises=True):
#     '''Closes the active project.'''
#     if not CONFIG['folders']['project']:
#         if not raises:
#             return
#         raise ProjectNotFound("No Brownie project currently open.")

#     # clear sources, build, coverage
#     sources.clear()
#     build.clear()
#     coverage.clear()

#     # remove objects from namespace
#     for name in sys.modules['brownie.project'].__all__.copy():
#         if name == "__brownie_import_all__":
#             continue
#         del sys.modules['brownie.project'].__dict__[name]
#         if '__brownie_import_all__' in sys.modules['__main__'].__dict__:
#             del sys.modules['__main__'].__dict__[name]
#     sys.modules['brownie.project'].__all__ = ['__brownie_import_all__']

#     # clear paths
#     try:
#         sys.path.remove(CONFIG['folders']['project'])
#     except ValueError:
#         pass
#     CONFIG['folders']['project'] = None


def compile_source(source):
    '''Compiles the given source code string and returns a list of
    ContractContainer instances.'''
    result = []
    for name, build_json in sources.compile_source(source).items():
        if build_json['type'] == "interface":
            continue
        result.append(ContractContainer(build_json))
    return result


def load(project_path=None, name=None):
    '''Loads a project and instantiates various related objects.

    Args:
        project_path: Path of the project to load. If None, will attempt to
                      locate a project using check_for_project()

    Returns a list of ContractContainer objects.
    '''
    # checks
    if CONFIG['folders']['project']:
        raise ProjectAlreadyLoaded(f"Project already loaded at {CONFIG['folders']['project']}")
    if project_path is None:
        project_path = check_for_project('.')
    if not project_path or not Path(project_path).joinpath("brownie-config.json").exists():
        raise ProjectNotFound("Could not find Brownie project")

    # paths
    project_path = Path(project_path).resolve()
    _create_folders(project_path)
    _add_to_sys_path(project_path)

    # load sources and build
    if name is None:
        name = project_path.name + " project"
        name = "".join(i for i in name.title() if i.isalpha())
    project = Project(project_path, name)
    setattr(sys.modules[__name__], name, project)
    return project
    # sources.load(project_path)
    # build.load(project_path)


def _create_folders(project_path):
    for path in [i for i in FOLDERS]:
        project_path.joinpath(path).mkdir(exist_ok=True)


def _add_to_sys_path(project_path):
    project_path = str(project_path)
    if project_path in sys.path:
        return
    sys.path.insert(0, project_path)


class Project:

    def __init__(self, project_path, name):
        self._project_path = Path(project_path)
        self._name = name

        self._compiler_config = load_project_compiler_config(project_path)
        solc_version = self._compiler_config['version']
        if solc_version:
            self._compiler_config['version'] = compiler.set_solc_version(solc_version)

        self._sources = Sources(project_path)
        self._build = Build(project_path, self._sources)

        # compile updated sources, update build
        changed = self._get_changed_contracts()
        build_json = compiler.compile_and_format(
            changed,
            solc_version=solc_version,
            optimize=self._compiler_config['optimize'],
            runs=self._compiler_config['runs'],
            evm_version=self._compiler_config['evm_version'],
            minify=self._compiler_config['minify_source'],
            silent=False
        )
        for data in build_json.values():
            self._build.add(data)

        # create objects, add to namespace
        self._contracts = _create_objects(self._build)
        for contract in self._contracts:
            setattr(self, contract._name, contract)

        import_key = f"__brownie_import_all_{name}__"
        setattr(self, import_key, True)
        self.__all__ = [import_key]+[i._name for i in self._contracts]
        sys.modules[f'brownie.project.{name}'] = self
        sys.modules['brownie.project'].__dict__[name] = self
        sys.modules['brownie.project'].__all__.append(name)

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

    def __repr__(self):
        items = [
            f"<{type(i).__name__} object '{color['string']}{i._name}{color}'>"
            for i in self._contracts
        ]
        return f"[{', '.join(items)}]"

    def load_config(self):
        load_project_config(self._project_path)

    def __getitem__(self, key):
        if isinstance(key, str):
            return next(i for i in self._contracts if i._name == key)
        return self._contracts[key]

    def __iter__(self):
        return iter(self._contracts)

    def __len__(self):
        return len(self._contracts)

    def dict(self):
        return dict((i._name, i) for i in self._contracts)

    def close(self):
        '''Closes the active project.'''
        name = self._name
        delattr(sys.modules[__name__], name)
        del sys.modules[f'brownie.project.{name}']
        # remove objects from namespace
        main = sys.modules['__main__']
        key = f"__brownie_import_all_{name}__"
        if getattr(main, name, None) == self:
            delattr(main, name)
        if hasattr(main, key):
            for item in self.__all__:
                if getattr(main, item, None) == getattr(self, item):
                    delattr(main, item)

        del sys.modules['brownie.project'].__dict__[name]
        sys.modules['brownie.project'].__all__.remove(name)

        # clear paths
        try:
            sys.path.remove(self._project_path)
        except ValueError:
            pass


def _create_objects(build):
    result = []
    for name, data in build.items():
        if not data['bytecode']:
            continue
        container = ContractContainer(data)
        result.append(container)
        # sys.modules['brownie.project'].__dict__[name] = container
        # sys.modules['brownie.project'].__all__.append(name)
        # # if running via brownie cli, add to brownie namespace
        # if ARGV['cli']:
        #     sys.modules['brownie'].__dict__[name] = container
        #     sys.modules['brownie'].__all__.append(name)
        # # if running via interpreter, add to main namespace if package was imported via from
        # elif '__brownie_import_all__' in sys.modules['__main__'].__dict__:
        #     sys.modules['__main__'].__dict__[name] = container
    return sorted(result, key=lambda k: k._name)
