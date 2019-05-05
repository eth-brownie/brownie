#!/usr/bin/python3

from pathlib import Path
import re

from brownie.types.types import _Singleton
from brownie._config import CONFIG


class Source(metaclass=_Singleton):

    def __init__(self):
        self._source = {}
        self._path = None
        self._data = {}
        self._inheritance_map = {}
    
    def _load(self):
        self. _path = Path(CONFIG['folders']['project']).joinpath('contracts')
        for path in [i for i in self._path.glob('**/*.sol') if "/_" not in str(i)]:
            self._source[str(path)] = path.open().read()
            self._get_contract_data(path)
        for name, inherited in [(k, v['inherited'].copy()) for k,v in self._data.items()]:
            self._data[name]['inherited'] = self._recursive_inheritance(inherited)

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
            print(inherited)
            inherited = set(i.strip() for i in inherited.split(', ') if i)
            print(inherited)
            self._data[name] = {
                'sourcePath': path,
                'type': type_,
                'inherited': inherited.union(re.findall("(?:;|{)\s*using *(\S*)(?= for)", source))
            }