#!/usr/bin/python3

from hashlib import sha1
import itertools
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


class Sources:

    def __init__(self, project_path):
        self._source = {}
        self._contracts = {}
        self._project_path = Path(project_path)
        for path in self._project_path.glob('contracts/**/*.sol'):
            if "/_" in str(path.as_posix()):
                continue
            with path.open() as fp:
                source = fp.read()
            path = str(path.relative_to(self._project_path).as_posix())
            self._source[path] = source
            self._contracts.update(self._get_contract_data(source, path))

    def _get_contract_data(self, full_source, path):
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
            if name in self._contracts and not self._contracts[name]['path'].startswith('<string-'):
                raise ContractExists(
                    f"Contract '{name}' already exists in the active project."
                )
            offset = (
                offset + next(i[1] for i in offset_map if i[0] <= offset),
                offset+len(source) + next(i[1] for i in offset_map if i[0] <= offset+len(source))
            )
            data[name] = {
                'path': path,
                'offset_map': offset_map,
                'minified': minified_source,
                'offset': offset
            }
        return data

    def get(self, name):
        '''Returns the source code file for the given name.

        Args:
            name: contract name or source code path

        Returns: source code as a string.'''
        if name in self._contracts:
            return self._source[self._contracts[name]['path']]
        return self._source[str(name)]

    def get_path_list(self):
        '''Returns a list of source code file paths for the active project.'''
        return list(self._source.keys())

    def get_contract_list(self):
        '''Returns a list of contract names for the active project.'''
        return list(self._contracts.keys())

    # def clear(self):
    #     '''Clears all currently loaded source files.'''
    #     self._source.clear()
    #     self._contracts.clear()

    def compile_source(self, source, solc_version=None, optimize=True, runs=200, evm_version=None):
        '''Compiles the given source and saves it with a path <string-X>, where
        X is a an integer increased with each successive call.

        Returns the build json data.'''

        path = next(
            f"<string-{i}>" for i in itertools.count() if f"<string-{i}>" not in self._source
        )
        self._source[path] = source
        self._contracts.update(self._get_contract_data(source, path))
        return compiler.compile_and_format(
            {path: source},
            solc_version=solc_version,
            optimize=optimize,
            runs=runs,
            evm_version=evm_version,
            silent=True
        )

    def get_hash(self, contract_name, minified):
        '''Returns a hash of the contract source code.'''
        try:
            if minified:
                return sha1(self._contracts[contract_name]['minified'].encode()).hexdigest()
            offset = self._contracts[contract_name]['offset']
            return sha1(self.get(contract_name)[slice(*offset)].encode()).hexdigest()
        except KeyError:
            return ""

    def get_source_path(self, contract_name):
        '''Returns the path to the source file where a contract is located.'''
        return self._contracts[contract_name]['path']

    def get_highlighted_source(self, path, offset, pad=3):
        '''Returns a highlighted section of source code.

        Args:
            path: Path to the source
            offset: Tuple of (start offset, stop offset)
            pad: Number of unrelated lines of code to include before and after

        Returns:
            str: Highlighted source code
            str: Source code path
            int: Line number that highlight begins on'''

        source = self._source[path]
        newlines = [i for i in range(len(source)) if source[i] == "\n"]
        try:
            pad_start = newlines.index(next(i for i in newlines if i >= offset[0]))
            pad_stop = newlines.index(next(i for i in newlines if i >= offset[1]))
        except StopIteration:
            return

        ln = (pad_start + 1, pad_stop + 1)
        pad_start = newlines[max(pad_start-(pad+1), 0)]
        pad_stop = newlines[min(pad_stop+pad, len(newlines)-1)]

        final = textwrap.indent(f"{color['dull']}"+textwrap.dedent(
            f"{source[pad_start:offset[0]]}{color}"
            f"{source[offset[0]:offset[1]]}{color['dull']}{source[offset[1]:pad_stop]}{color}"
        ), "    ")

        count = source[pad_start:offset[0]].count("\n")
        final = final.replace("\n ", f"\n{color['dull']} ", count)
        count = source[offset[0]:offset[1]].count('\n')
        final = final.replace('\n ', f"\n{color} ", count)
        count = source[offset[1]:pad_stop].count("\n")
        final = final.replace("\n ", f"\n{color['dull']} ", count)

        return final, path, ln

    def expand_offset(self, contract_name, offset):
        '''Converts an offset from source with comments removed, to one from the original source.'''
        offset_map = self._contracts[contract_name]['offset_map']

        return (
            offset[0] + next(i[1] for i in offset_map if i[0] <= offset[0]),
            offset[1] + next(i[1] for i in offset_map if i[0] < offset[1])
        )


def minify(source):
    '''Given contract source as a string, returns a minified version and an
    offset map.'''
    offsets = [(0, 0)]
    pattern = f"({'|'.join(MINIFY_REGEX_PATTERNS)})"
    for match in re.finditer(pattern, source):
        offsets.append((
            match.start() - offsets[-1][1],
            match.end() - match.start() + offsets[-1][1]
        ))
    return re.sub(pattern, "", source), offsets[::-1]


def is_inside_offset(inner, outer):
    '''Checks if the first offset is contained in the second offset

    Args:
        inner: inner offset tuple
        outer: outer offset tuple

    Returns: bool'''
    return outer[0] <= inner[0] <= inner[1] <= outer[1]
