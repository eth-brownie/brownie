#!/usr/bin/python3

from collections import defaultdict
import json
from pathlib import Path
import shutil

from brownie._singleton import _Singleton


REPLACE = ['active_network', 'networks']
IGNORE = ['active_network', 'folders']


class ConfigDict(dict):
    '''Dict subclass that prevents adding new keys when locked'''

    def __init__(self, values={}):
        self._locked = False
        super().__init__()
        self.update(values)

    def __setitem__(self, key, value):
        if self._locked and key not in self:
            raise KeyError(f"{key} is not a known config setting")
        if type(value) is dict:
            value = ConfigDict(value)
        super().__setitem__(key, value)

    def update(self, arg):
        for k, v in arg.items():
            self.__setitem__(k, v)

    def _lock(self):
        '''Locks the dict so that new keys cannot be added'''
        for v in [i for i in self.values() if type(i) is ConfigDict]:
            v._lock()
        self._locked = True

    def _unlock(self):
        '''Unlocks the dict so that new keys can be added'''
        for v in [i for i in self.values() if type(i) is ConfigDict]:
            v._unlock()
        self._locked = False


def _load_default_config():
    '''Loads the default configuration settings from brownie/data/config.json'''
    with Path(__file__).parent.joinpath("data/config.json").open() as fp:
        config = _Singleton("Config", (ConfigDict,), {})(json.load(fp))
    config['folders'] = {
        'brownie': str(Path(__file__).parent),
        'project': None
    }
    config['active_network'] = {'name': None}
    return config


def _get_project_config_file(project_path):
    project_path = Path(project_path)
    if not project_path.exists():
        raise ValueError("Project does not exist!")
    config_path = Path(project_path).joinpath("brownie-config.json")
    try:
        with config_path.open() as fp:
            return json.load(fp)
    except FileNotFoundError:
        shutil.copy(
            str(Path(CONFIG['folders']['brownie']).joinpath("data/config.json")),
            str(config_path)
        )
        print("WARNING: No config file found for this project. A new one has been created.")


def load_project_config(project_path):
    '''Loads configuration settings from a project's brownie-config.json'''
    config_data = _get_project_config_file(project_path)
    CONFIG._unlock()
    _recursive_update(CONFIG, config_data, [])
    CONFIG.setdefault('active_network', {'name': None})
    CONFIG._lock()


def load_project_compiler_config(project_path):
    if not project_path:
        return CONFIG['solc']
    config_data = _get_project_config_file(project_path)
    return config_data['solc']


def modify_network_config(network=None):
    '''Modifies the 'active_network' configuration settings'''
    CONFIG._unlock()
    try:
        if not network:
            network = CONFIG['network_defaults']['name']

        CONFIG['active_network'] = {
            **CONFIG['network_defaults'],
            **CONFIG['networks'][network]
        }
        CONFIG['active_network']['name'] = network

        if ARGV['cli'] == "test":
            CONFIG['active_network'].update(CONFIG['pytest'])
            if not CONFIG['active_network']['broadcast_reverting_tx']:
                print("WARNING: Reverting transactions will NOT be broadcasted.")
        return CONFIG['active_network']
    except KeyError:
        raise KeyError(f"Network '{network}' is not defined in config.json")
    finally:
        CONFIG._lock()


# merges project .json with brownie .json
def _recursive_update(original, new, base):
    for k in new:
        if type(new[k]) is dict and k in REPLACE:
            original[k] = new[k]
        elif type(new[k]) is dict and k in original:
            _recursive_update(original[k], new[k], base+[k])
        else:
            original[k] = new[k]
    for k in [i for i in original if i not in new and not set(base+[i]).intersection(IGNORE)]:
        print(
            f"WARNING: '{'.'.join(base+[k])}' not found in the config file for this project."
            " The default setting has been used."
        )


def update_argv_from_docopt(args):
    ARGV.update(dict((k.lstrip("-"), v) for k, v in args.items()))


# create argv object
ARGV = _Singleton("Argv", (defaultdict,), {})(lambda: None)

# load config
CONFIG = _load_default_config()
