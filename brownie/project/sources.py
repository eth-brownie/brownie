#!/usr/bin/python3

from hashlib import sha1
from pathlib import Path
import re

from brownie.cli.utils import color
from brownie.exceptions import ContractExists
from . import build, compiler

_source = {}
_contracts = {}


def get(name):
    '''Returns the source code file for the given name.

    Args:
        name: contract name or source code path

    Returns: source code as a string.'''
    if name in _contracts:
        return _source[_contracts[name]['path']]
    return _source[str(name)]


def get_path_list():
    '''Returns a list of source code file paths for the active project.'''
    return list(_source.keys())


def get_contract_list():
    '''Returns a list of contract names for the active project.'''
    return list(_contracts.keys())


def clear():
    '''Clears all currently loaded source files.'''
    _source.clear()
    _contracts.clear()


def load(project_path):
    '''Loads all source files for the given project path.'''
    clear()
    project_path = Path(project_path)
    for path in project_path.glob('contracts/**/*.sol'):
        if "/_" in str(path):
            continue
        source = path.open().read()
        path = str(path.relative_to(project_path))
        _source[path] = source
        _contracts.update(_get_contract_data(source, path))


def remove_comments(source):
    '''Given contract source as a string, returns the same contract with
    all the comments removed.'''
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
        offset = uncommented.index(source)
        if name in _contracts and not _contracts[name]['path'].startswith('<string-'):
            raise ContractExists(
                "Contract '{}' already exists in the active project.".format(name)
            )
        data[name] = {
            'path': str(path),
            'offset_map': offset_map,
            'uncommented': uncommented,
            'sha1': sha1(full_source.encode()).hexdigest(),
            'offset': (
                _commented_offset(offset_map, offset),
                _commented_offset(offset_map, offset + len(source))
            )
        }
    return data


def _commented_offset(offset_map, offset):
    '''Converts an offset from source with comments removed, to one from the original source.'''
    return offset + next(i[1] for i in offset_map if i[0] <= offset)


def compile_paths(paths):
    '''Compiles a list of contracts. The source code must have already been
    loaded via sources.load

    Args:
        paths: list of contract paths

    Returns: build json data
    '''
    to_compile = dict((k, _source[k]) for k in paths)
    return compiler.compile_contracts(to_compile)


def compile_source(source):
    '''Compiles the given source and saves it with a path <string-X>, where
    X is a an integer increased with each successive call.

    Returns the build json data.'''
    key = 1
    while "<string-{}".format(key) in _source:
        key += 1
    path = "<string-{}>".format(key)
    _source[path] = source
    _contracts.update(_get_contract_data(source, path))
    return compiler.compile_contracts({path: source}, True)


def get_hash(contract_name):
    '''Returns a hash of the contract source code.'''
    return _contracts[contract_name]['sha1']


def get_source_path(contract_name):
    '''Returns the path to the source file where a contract is located.'''
    return _contracts[contract_name]['path']


def get_fn(contract, offset):
    '''Given a contract name or path, and source offset tuple, returns the name of the
    associated function. Returns False if the offset spans multiple functions.'''
    if contract not in _contracts:
        contract = get_contract_name(contract, offset)
        if not contract:
            return False
    fn_offsets = build.get(contract)['fn_offsets']
    return next((i[0] for i in fn_offsets if is_inside_offset(offset, i[1])), False)


def get_fn_offset(contract, fn_name):
    '''Given a contract and function name, returns the source offsets of the function.'''
    try:
        if not contract not in _contracts:
            contract = next(
                k for k, v in build.items(contract) if
                fn_name in [i[0] for i in v['fn_offsets']]
            )
        return next(i for i in build.get(contract)['fn_offsets'] if i[0] == fn_name)[1]
    except StopIteration:
        raise ValueError("Unknown function '{}' in contract {}".format(fn_name, contract))


def get_contract_name(path, offset):
    '''Given a path and source offset tuple, returns the name of the contract.
    Returns False if the offset spans multiple contracts.'''
    return next((
        k for k, v in _contracts.items() if v['path'] == path and
        is_inside_offset(offset, v['offset'])
    ), False)


def get_highlighted_source(path, offset, pad=3):
    '''Returns a highlighted section of source code.

    Args:
        path: Path to the source
        offset: Tuple of (start offset, stop offset)
        pad: Number of unrelated lines of code to include before and after

    Returns:
        str - Highlighted source code
        str - Source code path
        int - Line number that highlight begins on
        str - Function name (or None)'''
    source = _source[path]
    newlines = [i for i in range(len(source)) if source[i] == "\n"]
    try:
        pad_start = newlines.index(next(i for i in newlines if i >= offset[0]))
        pad_stop = newlines.index(next(i for i in newlines if i >= offset[1]))
    except StopIteration:
        return ""
    ln = pad_start + 1
    pad_start = newlines[max(pad_start-(pad+1), 0)]
    pad_stop = newlines[min(pad_stop+pad, len(newlines)-1)]

    return "{0[dull]}{1}{0}{2}{0[dull]}{3}{0}".format(
        color,
        source[pad_start:offset[0]],
        source[offset[0]:offset[1]],
        source[offset[1]:pad_stop]
    ), path, ln, get_fn(path, offset)


def is_inside_offset(inner, outer):
    '''Checks if the first offset is contained in the second offset

    Args:
        inner: inner offset tuple
        outer: outer offset tuple

    Returns: bool'''
    return outer[0] <= inner[0] <= inner[1] <= outer[1]
