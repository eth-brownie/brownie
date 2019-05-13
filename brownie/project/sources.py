#!/usr/bin/python3

from hashlib import sha1
from pathlib import Path
import re

from brownie.types.types import _Singleton
from brownie._config import CONFIG


class Sources(metaclass=_Singleton):

    def __init__(self):
        self._source = {}
        self._uncommented_source = {}
        self._comment_offsets = {}
        self._path = None
        self._data = {}
        self._string_iter = 1

    def __getitem__(self, key):
        if key in self._data:
            return self._source[self._data[key]['sourcePath']]
        return self._source[str(key)]

    def _load(self):
        base_path = Path(CONFIG['folders']['project'])
        self. _path = base_path.joinpath('contracts')
        for path in [i.relative_to(base_path) for i in self._path.glob('**/*.sol')]:
            if "/_" in str(path):
                continue
            source = path.open().read()
            self._source[str(path)] = source
            self._remove_comments(path)
            self._get_contract_data(path)
        for name, inherited in [(k, v['inherited'].copy()) for k, v in self._data.items()]:
            self._data[name]['inherited'] = self._recursive_inheritance(inherited)

    def _remove_comments(self, path):
        source = self._source[str(path)]
        offsets = [(0, 0)]
        pattern = r"((?:\s*\/\/[^\n]*)|(?:\/\*[\s\S]*?\*\/))"
        for match in re.finditer(pattern, source):
            offsets.append((
                match.start() - offsets[-1][1],
                match.end() - match.start() + offsets[-1][1]
            ))
        self._uncommented_source[str(path)] = re.sub(pattern, "", source)
        self._comment_offsets[str(path)] = offsets[::-1]

    def _get_contract_data(self, path):
        contracts = re.findall(
            r"((?:contract|library|interface)[^;{]*{[\s\S]*?})\s*(?=contract|library|interface|$)",
            self._uncommented_source[str(path)]
        )
        for source in contracts:
            type_, name, inherited = re.findall(
                r"\s*(contract|library|interface)\s{1,}(\S*)\s*(?:is\s{1,}(.*?)|)(?:{)",
                source
            )[0]
            inherited = set(i.strip() for i in inherited.split(', ') if i)
            offset = self._uncommented_source[str(path)].index(source)
            self._data[name] = {
                'sourcePath': str(path),
                'type': type_,
                'inherited': inherited.union(re.findall(r"(?:;|{)\s*using *(\S*)(?= for)", source)),
                'sha1': sha1(source.encode()).hexdigest(),
                'fn_offsets': [],
                'offset': (
                    self._commented_offset(path, offset),
                    self._commented_offset(path, offset + len(source))
                )
            }
            if type_ == "interface":
                continue
            fn_offsets = []
            for idx, pattern in enumerate((
                # matches functions
                r"function\s*(\w*)[^{;]*{[\s\S]*?}(?=\s*function|\s*})",
                # matches public variables
                r"(?:{|;)\s*(?!function)(\w[^;]*(?:public\s*constant|public)\s*(\w*)[^{;]*)(?=;)"
            )):
                for match in re.finditer(pattern, source):
                    fn_offsets.append((
                        name+"."+(match.groups()[idx] or "<fallback>"),
                        self._commented_offset(path, match.start(idx) + offset),
                        self._commented_offset(path, match.end(idx) + offset)
                    ))
            self._data[name]['fn_offsets'] = sorted(fn_offsets, key=lambda k: k[1], reverse=True)

    def _commented_offset(self, path, offset):
        return offset + next(i[1] for i in self._comment_offsets[str(path)] if i[0] <= offset)

    def _recursive_inheritance(self, inherited):
        final = set(inherited)
        for name in inherited:
            final |= self._recursive_inheritance(self._data[name]['inherited'])
        return final

    def get_hash(self, contract_name):
        '''Returns a hash of the contract source code after comments have been removed.'''
        return self._data[contract_name]['sha1']

    def get_path(self, contract_name):
        '''Returns the path to the source file where a contract is located.'''
        return self._data[contract_name]['sourcePath']

    def get_type(self, contract_name):
        '''Returns the type of contract (contract, interface, library).'''
        return self._data[contract_name]['type']

    def get_fn(self, name, start, stop):
        '''Given a contract name, start and stop offset, returns the name of the
        associated function. Returns False if the offset spans multiple functions.'''
        if name not in self._data:
            name = self.get_contract_name(name, start, stop)
            if not name:
                return False
        offsets = self._data[name]['fn_offsets']
        if start < offsets[-1][1]:
            return False
        offset = next(i for i in offsets if start >= i[1])
        return False if stop > offset[2] else offset[0]

    def get_fn_offset(self, name, fn_name):
        '''Given a contract and function name, returns the source offsets of the function.'''
        try:
            if name not in self._data:
                name = next(
                    k for k, v in self._data.items() if v['sourcePath'] == str(name) and
                    fn_name in [i[0] for i in v['fn_offsets']]
                )
            return next(i for i in self._data[name]['fn_offsets'] if i[0] == fn_name)[1:3]
        except StopIteration:
            raise ValueError("Unknown function '{}' in contract {}".format(fn_name, name))

    def get_contract_name(self, path, start, stop):
        '''Given a path and source offsets, returns the name of the contract.
        Returns False if the offset spans multiple contracts.'''
        return next((
            k for k, v in self._data.items() if v['sourcePath'] == str(path) and
            v['offset'][0] <= start <= stop <= v['offset'][1]
        ), False)

    def inheritance_map(self):
        '''Returns a dict of sets in the format:

        {'contract name': {'inheritedcontract', 'inherited contract'..} }
        '''
        return dict((k, v['inherited'].copy()) for k, v in self._data.items())

    def add_source(self, source):
        '''Given source code as a string, adds it to the object and returns a path
        string formatted as "<string-X>" where X is a number that is incremented.
        '''
        path = "<string-{}>".format(self._string_iter)
        self._source[path] = source
        self._remove_comments(path)
        self._get_contract_data(path)
        self._string_iter += 1
        return path
