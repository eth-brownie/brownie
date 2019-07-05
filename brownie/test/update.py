#!/usr/bin/python3

import ast
from hashlib import sha1
import importlib
import json
from pathlib import Path
import warnings

from brownie.project import check_for_project
from brownie.project import build
from brownie.network.history import _ContractHistory


def get_ast_hash(path):
    '''Generates a hash based on the AST of a script.

    Args:
        path: path of the script to hash

    Returns: sha1 hash as bytes'''
    with Path(path).open() as f:
        ast_list = [ast.parse(f.read(), path)]
    base_path = str(check_for_project(path))
    for obj in [i for i in ast_list[0].body if type(i) in (ast.Import, ast.ImportFrom)]:
        if type(obj) is ast.Import:
            name = obj.names[0].name
        else:
            name = obj.module
        origin = importlib.util.find_spec(name).origin
        if base_path in origin:
            with open(origin) as f:
                ast_list.append(ast.parse(f.read(), origin))
    dump = "\n".join(ast.dump(i) for i in ast_list)
    return sha1(dump.encode()).hexdigest()


class UpdateManager:

    def __init__(self, path):
        self.path = path
        self.conf_hashes = {}
        try:
            with open(path) as fp:
                hashes = json.load(fp)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            hashes = {'tests': {}, 'contracts': {}}
        self.tests = dict((k, v) for k, v in hashes['tests'].items() if Path(k).exists())
        self.contracts = {}
        for name, hash_ in hashes['contracts'].items():
            if build.contains(name) and build.get(name)['bytecodeSha1'] == hash_:
                self.contracts[name] = hash_

    def add_setup(self, path):
        path = str(path)
        self.conf_hashes[path] = get_ast_hash(path)

    def set_ignore(self, paths):
        self.ignore = paths
        for path in [i for i in paths if i in self.tests]:
            del self.tests[path]

    def _get_hash(self, path):
        hash_ = get_ast_hash(path)
        for confpath in filter(lambda k: k in path, sorted(self.conf_hashes)):
            hash_ += confpath
        return sha1(hash_.encode()).hexdigest()

    def check_module(self, path):
        path = str(path)
        hash_ = self._get_hash(path)
        print(path in self.tests)
        if path not in self.tests or self.tests[path]['hash'] != hash_:
            return False
        for name in self.tests[path]['contracts']:
            if not build.contains(name) or build.get(name)['bytecodeSha1'] != self.contracts[name]:
                del self.tests[path]
                return False
        return True

    def update_module(self, path):
        path = str(path)
        if path in self.ignore:
            warnings.warn(
                f"Improper use of isolation fixture in {path}, "
                "fixture should be applied to all tests"
            )
            return
        dependencies = _ContractHistory().dependencies()
        for name in [i for i in dependencies if i not in self.contracts]:
            self.contracts[name] = build.get(name)['bytecodeSha1']
        self.tests[path] = {
            'hash': self._get_hash(path),
            'contracts': dependencies
        }
        with open(self.path, 'w') as fp:
            json.dump({'tests': self.tests, 'contracts': self.contracts}, fp, indent=2)
