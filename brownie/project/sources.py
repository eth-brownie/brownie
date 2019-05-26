#!/usr/bin/python3

from hashlib import sha1
from pathlib import Path
import re

from brownie.cli.utils import color
from brownie.exceptions import ContractExists
from . import compiler

_source = {}
_data = {}


def get(name):
    if name in _data:
        return _source[_data[name]['sourcePath']]
    return _source[str(name)]


def clear():
    _source.clear()
    _data.clear()


def load(project_path):
    clear()
    project_path = Path(project_path)
    for path in project_path.glob('contracts/**/*.sol'):
        if "/_" in str(path):
            continue
        source = path.open().read()
        path = str(path.relative_to(project_path))
        _source[path] = source
        _data.update(_get_contract_data(source, path))
    for name, inherited in [(k, v['inherited'].copy()) for k, v in _data.items()]:
        _data[name]['inherited'] = _recursive_inheritance(inherited)


def remove_comments(source):
    offsets = [(0, 0)]
    pattern = r"((?:\s*\/\/[^\n]*)|(?:\/\*[\s\S]*?\*\/))"
    for match in re.finditer(pattern, source):
        offsets.append((
            match.start() - offsets[-1][1],
            match.end() - match.start() + offsets[-1][1]
        ))
    return re.sub(pattern, "", source), offsets[::-1]


def _get_contract_data(full_source, path):
    uncommented, offset_map = remove_comments(full_source)
    contracts = re.findall(
        r"((?:contract|library|interface)[^;{]*{[\s\S]*?})\s*(?=contract|library|interface|$)",
        uncommented
    )
    data = {}
    for source in contracts:
        type_, name, inherited = re.findall(
            r"\s*(contract|library|interface)\s{1,}(\S*)\s*(?:is\s{1,}(.*?)|)(?:{)",
            source
        )[0]
        inherited = set(i.strip() for i in inherited.split(', ') if i)
        offset = uncommented.index(source)
        if name in _data and not _data[name]['sourcePath'].startswith('<string-'):
            raise ContractExists(
                "Contract '{}' already exists in the active project.".format(name)
            )
        data[name] = {
            'sourcePath': str(path),
            'type': type_,
            'inherited': inherited.union(re.findall(r"(?:;|{)\s*using *(\S*)(?= for)", source)),
            'sha1': sha1(full_source.encode()).hexdigest(),
            'fn_offsets': [],
            'offset': (
                _commented_offset(offset_map, offset),
                _commented_offset(offset_map, offset + len(source))
            )
        }
        if type_ == "interface":
            continue
        data[name]['fn_offsets'] = _get_fn_offsets(source, name, offset, offset_map)
    return data


def _get_fn_offsets(source, contract_name, base_offset, offset_map):
    fn_offsets = []
    for idx, pattern in enumerate((
        # matches functions
        r"function\s*(\w*)[^{;]*{[\s\S]*?}(?=\s*function|\s*})",
        # matches public variables
        r"(?:{|;)\s*(?!function)(\w[^;]*(?:public\s*constant|public)\s*(\w*)[^{;]*)(?=;)"
    )):
        for match in re.finditer(pattern, source):
            fn_offsets.append((
                contract_name+"."+(match.groups()[idx] or "<fallback>"),
                _commented_offset(offset_map, match.start(idx) + base_offset),
                _commented_offset(offset_map, match.end(idx) + base_offset)
            ))
    return sorted(fn_offsets, key=lambda k: k[1], reverse=True)


def _commented_offset(offset_map, offset):
    return offset + next(i[1] for i in offset_map if i[0] <= offset)


def _recursive_inheritance(inherited):
    final = set(inherited)
    for name in inherited:
        final |= _recursive_inheritance(_data[name]['inherited'])
    return final


def compile_paths(paths):
    to_compile = dict((k, _source[k]) for k in paths)
    return compiler.compile_contracts(to_compile)


def compile_source(source):
    key = 1
    while "<string-{}".format(key) in _source:
        key += 1
    path = "<string-{}>".format(key)
    _source[path] = source
    _data.update(_get_contract_data(source, path))
    return compiler.compile_contracts({path: source}, True)


def get_hash(contract_name):
    '''Returns a hash of the contract source code.'''
    return _data[contract_name]['sha1']


def get_path(contract_name):
    '''Returns the path to the source file where a contract is located.'''
    return _data[contract_name]['sourcePath']


def get_type(contract_name):
    '''Returns the type of contract (contract, interface, library).'''
    return _data[contract_name]['type']


def get_fn(contract, start, stop):
    '''Given a contract name or path, start and stop offset, returns the name of the
    associated function. Returns False if the offset spans multiple functions.'''
    if contract not in _data:
        contract = get_contract_name(contract, start, stop)
        if not contract:
            return False
    offsets = _data[contract]['fn_offsets']
    if start < offsets[-1][1]:
        return False
    offset = next(i for i in offsets if start >= i[1])
    return False if stop > offset[2] else offset[0]


def get_fn_offset(self, contract, fn_name):
    '''Given a contract and function name, returns the source offsets of the function.'''
    try:
        if contract not in _data:
            contract = next(
                k for k, v in _data.items() if v['sourcePath'] == str(contract) and
                fn_name in [i[0] for i in v['fn_offsets']]
            )
        return next(i for i in _data[contract]['fn_offsets'] if i[0] == fn_name)[1:3]
    except StopIteration:
        raise ValueError("Unknown function '{}' in contract {}".format(fn_name, contract))


def get_contract_name(path, start, stop):
    '''Given a path and source offsets, returns the name of the contract.
    Returns False if the offset spans multiple contracts.'''
    return next((
        k for k, v in _data.items() if v['sourcePath'] == str(path) and
        v['offset'][0] <= start <= stop <= v['offset'][1]
    ), False)


def get_inheritance_map(contract_name=None):
    '''Returns a dict of sets in the format:

    {'contract name': {'inheritedcontract', 'inherited contract'..} }
    '''
    if contract_name:
        return _data[contract_name]['inherited'].copy()
    return dict((k, v['inherited'].copy()) for k, v in _data.items())


def get_highlighted_source(path, start, stop, pad=3):
    '''Returns a highlighted section of source code.

    Args:
        path: Path to the source
        start: Start offset
        stop: Stop offset
        pad: Number of unrelated lines of code to include before and after

    Returns:
        str - Highlighted source code
        str - Source code path
        int - Line number that highlight begins on
        str - Function name (or None)'''
    source = _source[path]
    newlines = [i for i in range(len(source)) if source[i] == "\n"]
    try:
        pad_start = newlines.index(next(i for i in newlines if i >= start))
        pad_stop = newlines.index(next(i for i in newlines if i >= stop))
    except StopIteration:
        return ""
    ln = pad_start + 1
    pad_start = newlines[max(pad_start-(pad+1), 0)]
    pad_stop = newlines[min(pad_stop+pad, len(newlines)-1)]

    return "{0[dull]}{1}{0}{2}{0[dull]}{3}{0}".format(
        color,
        source[pad_start:start],
        source[start:stop],
        source[stop:pad_stop]
    ), path, ln, get_fn(path, start, stop)
