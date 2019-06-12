#!/usr/bin/python3

from hashlib import sha1
from pathlib import Path
import re
import textwrap

from . import compiler
from brownie.cli.utils import color
from brownie.exceptions import ContractExists


MINIFY_REGEX_PATTERNS = [
    r"(?:\s*\/\/[^\n]*)|(?:\/\*[\s\S]*?\*\/)",                   # comments
    r"(?<=\n)\s{1,}|[ \t]{1,}(?=\n)",                            # leading / trailing whitespace
    r"(?<=[^\w\s])[ \t]{1,}(?=\w)|(?<=\w)[ \t]{1,}(?=[^\w\s])"  # whitespace between expressions
]

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


def minify(source):
    '''Given contract source as a string, returns a minified version and an
    offset map.'''
    offsets = [(0, 0)]
    pattern = "({})".format("|".join(MINIFY_REGEX_PATTERNS))
    for match in re.finditer(pattern, source):
        offsets.append((
            match.start() - offsets[-1][1],
            match.end() - match.start() + offsets[-1][1]
        ))
    return re.sub(pattern, "", source), offsets[::-1]


def _get_contract_data(full_source, path):
    minified_source, offset_map = minify(full_source)
    contracts = re.findall(
        r"((?:contract|library|interface)[^;{]*{[\s\S]*?})\s*(?=contract|library|interface|$)",
        minified_source
    )
    data = {}
    for source in contracts:
        type_, name, inherited = re.findall(
            r"\s*(contract|library|interface)\s{1,}(\S*)\s*(?:is\s{1,}(.*?)|)(?:{)",
            source
        )[0]
        offset = minified_source.index(source)
        if name in _contracts and not _contracts[name]['path'].startswith('<string-'):
            raise ContractExists(
                "Contract '{}' already exists in the active project.".format(name)
            )
        data[name] = {
            'path': str(path),
            'offset_map': offset_map,
            'minified': minified_source,
            'offset': (
                offset + next(i[1] for i in offset_map if i[0] <= offset),
                offset+len(source) + next(i[1] for i in offset_map if i[0] <= offset+len(source))
            )
        }
    return data


def compile_paths(paths, optimize=True, runs=200, minify=False, silent=False):
    '''Compiles a list of contracts. The source code must have already been
    loaded via sources.load

    Args:
        paths: list of contract paths

    Returns: build json data
    '''
    to_compile = dict((k, _source[k]) for k in paths)
    return compiler.compile_and_format(
        to_compile,
        optimize=optimize,
        runs=runs,
        minify=minify,
        silent=silent
    )


def compile_source(source, optimize=True, runs=200):
    '''Compiles the given source and saves it with a path <string-X>, where
    X is a an integer increased with each successive call.

    Returns the build json data.'''
    key = 1
    while "<string-{}".format(key) in _source:
        key += 1
    path = "<string-{}>".format(key)
    _source[path] = source
    _contracts.update(_get_contract_data(source, path))
    return compiler.compile_and_format({path: source}, optimize=optimize, runs=runs, silent=True)


def get_hash(contract_name, minified):
    '''Returns a hash of the contract source code.'''
    try:
        if minified:
            return sha1(_contracts[contract_name]['minified'].encode()).hexdigest()
        offset = _contracts[contract_name]['offset']
        return sha1(get(contract_name)[slice(*offset)].encode()).hexdigest()
    except KeyError:
        return ""


def get_source_path(contract_name):
    '''Returns the path to the source file where a contract is located.'''
    return _contracts[contract_name]['path']


def get_highlighted_source(path, offset, pad=3):
    '''Returns a highlighted section of source code.

    Args:
        path: Path to the source
        offset: Tuple of (start offset, stop offset)
        pad: Number of unrelated lines of code to include before and after

    Returns:
        str: Highlighted source code
        str: Source code path
        int: Line number that highlight begins on'''

    source = _source[path]
    newlines = [i for i in range(len(source)) if source[i] == "\n"]
    try:
        pad_start = newlines.index(next(i for i in newlines if i >= offset[0]))
        pad_stop = newlines.index(next(i for i in newlines if i >= offset[1]))
    except StopIteration:
        return
    ln = pad_start + 1
    pad_start = newlines[max(pad_start-(pad+1), 0)]
    pad_stop = newlines[min(pad_stop+pad, len(newlines)-1)]

    final = "{1}{0}{2}{0[dull]}{3}{0}".format(
        color,
        source[pad_start:offset[0]],
        source[offset[0]:offset[1]],
        source[offset[1]:pad_stop]
    )
    final = color('dull')+textwrap.indent(textwrap.dedent(final), "    ")
    return final, path, ln


def is_inside_offset(inner, outer):
    '''Checks if the first offset is contained in the second offset

    Args:
        inner: inner offset tuple
        outer: outer offset tuple

    Returns: bool'''
    return outer[0] <= inner[0] <= inner[1] <= outer[1]


def expand_offset(contract_name, offset):
    '''Converts an offset from source with comments removed, to one from the original source.'''
    offset_map = _contracts[contract_name]['offset_map']

    return (
        offset[0] + next(i[1] for i in offset_map if i[0] <= offset[0]),
        offset[1] + next(i[1] for i in offset_map if i[0] < offset[1])
    )
