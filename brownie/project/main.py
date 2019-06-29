#!/usr/bin/python3

from io import BytesIO
from pathlib import Path
import requests
import shutil
import sys
import zipfile

from brownie.network.contract import ContractContainer
from brownie.exceptions import ProjectAlreadyLoaded, ProjectNotFound
from brownie.project import build, sources, compiler
from brownie._config import ARGV, CONFIG, load_project_config

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
    CONFIG['folders']['project'] = str(project_path)
    _add_to_sys_path(project_path)
    return str(project_path)


def pull(project_name, project_path=None, ignore_subfolder=False):
    '''Initializes a new project via a template. Templates are downloaded from
    https://www.github.com/brownie-mixes

    Args:
        project_path: Path to initialize the project at.
        ignore_subfolders: If True, will not raise if initializing in a project subfolder.

    Returns the path to the project as a string.
    '''
    project_name = project_name.replace('-mix', '')
    url = MIXES_URL.format(project_name)
    if project_path is None:
        project_path = Path('.').joinpath(project_name)
    project_path = _new_checks(project_path, ignore_subfolder)
    if project_path.exists():
        raise FileExistsError("Folder already exists - {}".format(project_path))

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


def close(raises=True):
    '''Closes the active project.'''
    if not CONFIG['folders']['project']:
        if not raises:
            return
        raise ProjectNotFound("No Brownie project currently open.")

    # clear sources and build
    sources.clear()
    build.clear()

    # remove objects from namespace
    for name in sys.modules['brownie.project'].__all__.copy():
        if name == "__brownie_import_all__":
            continue
        del sys.modules['brownie.project'].__dict__[name]
        if '__brownie_import_all__' in sys.modules['__main__'].__dict__:
            del sys.modules['__main__'].__dict__[name]
    sys.modules['brownie.project'].__all__ = ['__brownie_import_all__']

    # clear paths
    sys.path.remove(CONFIG['folders']['project'])
    CONFIG['folders']['project'] = None


def compile_source(source):
    '''Compiles the given source code string and returns a list of
    ContractContainer instances.'''
    result = []
    for name, build_json in sources.compile_source(source).items():
        if build_json['type'] == "interface":
            continue
        result.append(ContractContainer(build_json))
    return result


def load(project_path=None):
    '''Loads a project and instantiates various related objects.

    Args:
        project_path: Path of the project to load. If None, will attempt to
                      locate a project using check_for_project()

    Returns a list of ContractContainer objects.
    '''
    # checks
    if CONFIG['folders']['project']:
        raise ProjectAlreadyLoaded(
            "Project has already been loaded at {}".format(CONFIG['folders']['project'])
        )
    if project_path is None:
        project_path = check_for_project('.')
    if not project_path or not Path(project_path).joinpath("brownie-config.json").exists():
        raise ProjectNotFound("Could not find Brownie project")

    # paths
    project_path = Path(project_path).resolve()
    _create_folders(project_path)
    _add_to_sys_path(project_path)

    # load config
    load_project_config(project_path)
    CONFIG['solc']['version'] = compiler.set_solc_version(CONFIG['solc']['version'])

    # load sources and build
    sources.load(project_path)
    build.load(project_path)

    # compare build, erase as needed
    changed_paths = _get_changed_contracts()

    # compile sources, update build
    build_json = sources.compile_paths(
        changed_paths,
        optimize=CONFIG['solc']['optimize'],
        runs=CONFIG['solc']['runs'],
        minify=CONFIG['solc']['minify_source']
    )
    for data in build_json.values():
        build.add(data)

    # create objects, add to namespace
    return _create_objects()


def _create_folders(project_path):
    for path in [i for i in FOLDERS]:
        project_path.joinpath(path).mkdir(exist_ok=True)


def _get_changed_contracts():
    changed = [i for i in sources.get_contract_list() if _compare_build_json(i)]
    final = set(changed)
    for contract_name in changed:
        final.update(build.get_dependents(contract_name))
    for name in [i for i in final if build.contains(i)]:
        build.delete(name)
    return set(sources.get_source_path(i) for i in final)


def _compare_build_json(contract_name):
    try:
        build_json = build.get(contract_name)
    except KeyError:
        return True
    return (
        build_json['compiler'] != CONFIG['solc'] or
        build_json['sha1'] != sources.get_hash(contract_name, CONFIG['solc']['minify_source'])
    )


def _create_objects():
    result = []
    for name, data in build.items():
        if not data['bytecode']:
            continue
        container = ContractContainer(data)
        result.append(container)
        sys.modules['brownie.project'].__dict__[name] = container
        sys.modules['brownie.project'].__all__.append(name)
        # if running via brownie cli, add to brownie namespace
        if ARGV['cli']:
            sys.modules['brownie'].__dict__[name] = container
            sys.modules['brownie'].__all__.append(name)
        # if running via interpreter, add to main namespace if package was imported via from
        elif '__brownie_import_all__' in sys.modules['__main__'].__dict__:
            sys.modules['__main__'].__dict__[name] = container
    return result


def _add_to_sys_path(project_path):
    project_path = str(project_path)
    if project_path in sys.path:
        return
    sys.path.insert(0, project_path)
