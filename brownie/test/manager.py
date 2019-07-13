#!/usr/bin/python3

import ast
import atexit
from hashlib import sha1
import importlib
import json
from pathlib import Path

from brownie.cli.utils import color
from brownie.network.history import TxHistory, _ContractHistory
from brownie.project import build, check_for_project
from brownie.test import coverage
from brownie._config import ARGV

STATUS_COLORS = {
    '.': "green",
    's': "yellow",
    'F': "red"
}

STATUS_SYMBOLS = {
    'skipped': 's',
    'passed': '.',
    'failed': 'F'
}

history = TxHistory()
_contracts = _ContractHistory()


def get_ast_hash(path):
    '''Generates a hash based on the AST of a script.

    Args:
        path: path of the script to hash

    Returns: sha1 hash as bytes'''
    with Path(path).open() as fp:
        ast_list = [ast.parse(fp.read(), path)]
    base_path = str(check_for_project(path))
    for obj in [i for i in ast_list[0].body if type(i) in (ast.Import, ast.ImportFrom)]:
        if type(obj) is ast.Import:
            name = obj.names[0].name
        else:
            name = obj.module
        origin = importlib.util.find_spec(name).origin
        if base_path in origin:
            with open(origin) as fp:
                ast_list.append(ast.parse(fp.read(), origin))
    dump = "\n".join(ast.dump(i) for i in ast_list)
    return sha1(dump.encode()).hexdigest()


class TestManager:

    def __init__(self, path):
        self.active = None
        self.count = 0
        self.results = None
        self.path = path
        self.conf_hashes = dict(
            (self._path(i.parent), get_ast_hash(i)) for i in Path(path).glob('tests/**/conftest.py')
        )
        try:
            with path.joinpath('build/tests.json').open() as fp:
                hashes = json.load(fp)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            hashes = {'tests': {}, 'contracts': {}, 'tx': {}}

        self.tests = dict(
            (k, v) for k, v in hashes['tests'].items() if
            Path(k).exists() and self._get_hash(k) == v['sha1']
        )
        self.contracts = dict((k, v['bytecodeSha1']) for k, v in build.items() if v['bytecode'])
        changed_contracts = set(
            k for k, v in hashes['contracts'].items() if
            k not in self.contracts or v != self.contracts[k]
        )
        if changed_contracts:
            for txhash, coverage_eval in hashes['tx'].items():
                if not changed_contracts.intersection(coverage_eval.keys()):
                    coverage[txhash] = coverage_eval
            self.tests = dict(
                (k, v) for k, v in self.tests.items() if v['isolated'] is not False
                and not changed_contracts.intersection(v['isolated'])
            )
        else:
            for txhash, coverage_eval in hashes['tx'].items():
                coverage[txhash] = coverage_eval
        atexit.register(self._save_json)
        return

    def _path(self, path):
        return str(Path(path).absolute().relative_to(self.path))

    def set_isolated_modules(self, paths):
        self.isolated = set(self._path(i) for i in paths)

    def _get_hash(self, path):
        hash_ = get_ast_hash(path)
        for confpath in filter(lambda k: k in path, sorted(self.conf_hashes)):
            hash_ += self.conf_hashes[confpath]
        return sha1(hash_.encode()).hexdigest()

    def check_updated(self, path):
        path = self._path(path)
        if path not in self.tests or not self.tests[path]['isolated']:
            return False
        if ARGV['coverage'] and not self.tests[path]['coverage']:
            return False
        return True

    def module_completed(self, path):
        path = self._path(path)
        isolated = False
        if path in self.isolated:
            isolated = [i for i in _contracts.dependencies() if i in self.contracts]
        self.tests[path] = {
            'sha1': self._get_hash(path),
            'isolated': isolated,
            'coverage': ARGV['coverage'] or (path in self.tests and self.tests[path]['coverage']),
            'txhash': history.get_coverage_hashes(),
            'results': "".join(self.results)
        }

    def _save_json(self):
        report = {
            'tests': self.tests,
            'contracts': self.contracts,
            'tx': coverage.get()
        }
        with self.path.joinpath('build/tests.json').open('w') as fp:
            json.dump(report, fp, indent=2, sort_keys=True, default=sorted)

    def set_active(self, path):
        path = self._path(path)
        if path == self.active:
            self.count += 1
            return
        self.active = path
        self.count = 0
        if path in self.tests and ARGV['update']:
            self.results = list(self.tests[path]['results'])
        else:
            self.results = []

    def check_status(self, report):
        if report.when == "setup":
            if len(self.results) < self.count+1:
                self.results.append("s" if report.skipped else None)
            if report.skipped:
                key = STATUS_COLORS[self.results[self.count]]
                return report.outcome, f"{color[key]}s", report.outcome.upper()
            if report.failed:
                self.results[self.count] = "F"
                return "error", "E", "ERROR"
            return "", "", ""
        if report.when == "teardown":
            if report.failed:
                self.results[self.count] = "F"
                return "error", "E", "ERROR"
            elif report.skipped and self.results[self.count] == "s":
                return "skipped", "s", "SKIPPED"
            return "", "", ""
        self.results[self.count] = STATUS_SYMBOLS[report.outcome]
        return report.outcome, STATUS_SYMBOLS[report.outcome], report.outcome.upper()
