#!/usr/bin/python3


from pathlib import Path
import json



class StrictDict(dict):

    def __init__(self, values={}):
        self._locked = False
        super().__init__()
        self.update(values)

    def __setitem__(self, key, value):
        if self._locked and key not in self:
            raise KeyError("{} is not a known config setting".format(key))
        if type(value) is dict:
            value = StrictDict(value)
        super().__setitem__(key, value)

    def update(self, arg):
        for k, v in arg.items():
            self.__setitem__(k, v)

    def _lock(self):
        for v in [i for i in self.values() if type(i) is StrictDict]:
            v._lock()
        self._locked = True

    def _unlock(self):
        for v in [i for i in self.values() if type(i) is StrictDict]:
            v._unlock()
        self._locked = False


def load_config():
    path = Path(__file__).parents[1].joinpath("config.json")
    config = StrictDict(json.load(path.open()))
    config['folders'] = {
        'brownie': str(Path(__file__).parents[1]),
        'project': None
    }
    return config

def update_config(network = None):
    CONFIG._unlock()
    if CONFIG['folders']['project']:
        path = Path(CONFIG['folders']['project']).joinpath("brownie-config.json")
        if path.exists():
            _recursive_update(CONFIG, json.load(path.open()))
    # modify network settings
    if not network:
        network = CONFIG['network_defaults']['name']
    try:
        CONFIG['active_network'] = CONFIG['networks'][network]
        CONFIG['active_network']['name'] = network
        for key, value in CONFIG['network_defaults'].items():
            if key not in CONFIG['active_network']:
                CONFIG['active_network'][key] = value
        if 'persist' not in CONFIG['active_network']:
            CONFIG['active_network']['persist'] = False
    except KeyError:
        raise KeyError("Network '{}' is not defined in config.json".format(network))
    CONFIG._lock()


# merges project .json with brownie .json
def _recursive_update(original, new):
    for k in new:
        if type(new[k]) is dict and k in original:
            _recursive_update(original[k], new[k])
        else:
            original[k] = new[k]


CONFIG = load_config()
update_config()