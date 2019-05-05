#!/usr/bin/python3

from pathlib import Path
import re
from hashlib import sha1

from brownie.types.types import _Singleton
from brownie._config import CONFIG


class Source(metaclass=_Singleton):

    def __init__(self):
        self._source = {}
        self._path = None
        self._data = {}
        self._inheritance_map = {}
        self._string_iter = 1
    
    def _load(self):
        self. _path = Path(CONFIG['folders']['project']).joinpath('contracts')
        for path in [i for i in self._path.glob('**/*.sol') if "/_" not in str(i)]:
            self._source[str(path)] = path.open().read()
            self._get_contract_data(path)
        for name, inherited in [(k, v['inherited'].copy()) for k,v in self._data.items()]:
            self._data[name]['inherited'] = self._recursive_inheritance(inherited)

    def _get_contract_data(self, path):
        contracts = re.findall(
            "((?:contract|library|interface)[\s\S]*?})\s*(?=contract|library|interface|$)",
            self.remove_comments(path)
        )
        for source in contracts:
            type_, name, inherited = re.findall(
                "\s*(contract|library|interface) (\S*) (?:is (.*?)|)(?: *{)",
                source
            )[0]
            inherited = set(i.strip() for i in inherited.split(', ') if i)
            self._data[name] = {
                'sourcePath': path,
                'type': type_,
                'inherited': inherited.union(re.findall("(?:;|{)\s*using *(\S*)(?= for)", source)),
                'sha1': sha1(source.encode()).hexdigest()
            }

    def _recursive_inheritance(self, inherited):
        final = set(inherited)
        for name in inherited:
            final |= self._recursive_inheritance(self._data[name]['inherited'])
        return final

    def remove_comments(self, path):
        return re.sub(
            "((?:\s*\/\/[^\n]*)|(?:\/\*[\s\S]*?\*\/))",
            "",
            self._source[str(path)]
        )
    
    def get_hash(self, contract_name):
        return self._data[contract_name]['sha1']

    def get_path(self, contract_name):
        return self._data[contract_name]['sourcePath']

    def get_type(self, contract_name):
        return self._data[contract_name]['type']
    
    def inheritance_map(self):
        return dict((k, v['inherited'].copy()) for k,v in self._data.items())

    def __getitem__(self, key):
        if key in self._data:
            return self._source[self._data[key]['sourcePath']]
        return self._source[str(key)]

    def add_source(self, source):
        path = "<string-{}>".format(self._string_iter)
        self._source[path] = source
        self._get_contract_data(path)
        self._string_iter += 1
        return path