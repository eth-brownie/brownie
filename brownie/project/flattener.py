
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, Final, Iterator, Set, final

import eth_utils.toolz

from brownie.utils.toposort import toposort_flatten

# Patten matching Solidity `import-directive`, capturing path component
# https://docs.soliditylang.org/en/latest/grammar.html#a4.SolidityParser.importDirective
IMPORT_PATTERN: Final = re.compile(
    r"(?<=\n)?import(?P<prefix>.*)(?P<quote>[\"'])(?P<path>.*)(?P=quote)(?P<suffix>.*)(?=\n)"
)
PRAGMA_PATTERN: Final = re.compile(r"^pragma.*;$", re.MULTILINE)
LICENSE_PATTERN: Final = re.compile(r"^// SPDX-License-Identifier: (.*)$", re.MULTILINE)


# C Constants

_Path: Final = Path

_defaultdict: Final = defaultdict

_sub: Final = re.sub

_mapcat: Final = eth_utils.toolz.mapcat


@final
class Flattener:
    """Brownie's Robust Solidity Flattener."""

    def __init__(
        self,
        primary_source_fp: str,
        contract_name: str,
        remappings: Dict[str, str],
        compiler_settings: Dict[str, Any],
    ) -> None:
        self.sources: Final[Dict[str, str]] = {}
        self.dependencies: Final[DefaultDict[str, Set[str]]] = _defaultdict(set)
        self.compiler_settings: Final = compiler_settings
        self.contract_name: Final = contract_name
        self.contract_file: Final = self.path_to_name(primary_source_fp)
        self.remappings: Final = remappings

        self.traverse(primary_source_fp)

        license_search = _LICENSE_PATTERN_SEARCH(self.path_to_name(primary_source_fp))
        self.license: Final = license_search.group(1) if license_search else "NONE"

    @classmethod
    def path_to_name(cls, pth: str) -> str:
        """Turn the full-path of every Solidity file to a unique shorten name.

        Note, that sometimes there could be several different files with the same name in a project,
        so these files should keep uniq name to correct verification.
        """
        return "contracts/" + pth.split("/contracts/")[1]

    def traverse(self, fp: str) -> None:
        """Traverse a contract source files dependencies.

        Files are read in, import statement path components are substituted for their absolute
        path, and the modified source is saved along with it's dependencies.

        Args:
            fp: The contract source file to traverse, if it's already been traversed, return early.
        """
        # if already traversed file, return early
        name = self.path_to_name(fp)
        fp_obj = _Path(fp)
        if name in self.sources:
            return

        # read in the source file
        source = fp_obj.read_text()

        # path sanitization lambda fn
        sanitize = lambda path: self.make_import_absolute(  # noqa: E731
            self.remap_import(path), fp_obj.parent.as_posix()
        )
        # replacement function for re.sub, we just sanitize the path
        repl = (  # noqa: E731
            lambda m: f'import{m.group("prefix")}'
            + f'"{self.path_to_name(sanitize(m.group("path")))}"'
            + f'{m.group("suffix")}'
        )
        self.sources[name] = _IMPORT_PATTERN_SUB(repl, source)
        if fp_obj.name not in self.dependencies:
            self.dependencies[name] = set()

        # traverse dependency files - can circular imports happen?
        for m in _IMPORT_PATTERN_FINDITER(source):
            import_path = sanitize(m.group("path"))
            self.dependencies[name].add(self.path_to_name(import_path))
            self.traverse(import_path)

    @property
    def flattened_source(self) -> str:
        """The flattened source code for use verifying."""
        flattened_deps = toposort_flatten(self.dependencies)
        # all source files in the correct order for concatenation
        sources = [self.sources[x] for x in flattened_deps]

        pragmas_iter: Iterator[str] = _mapcat(_PRAGMA_PATTERN_FINDALL, sources)
        # all pragma statements, we already have the license used + know which compiler
        # version is used via the build info
        pragmas = set(s.strip() for s in pragmas_iter)

        # now we go through and remove all imports/pragmas/license stuff, then flatten
        flat = (
            "\n".join(pragma for pragma in pragmas if "pragma solidity" not in pragma)
            + "\n\n"
            + "\n".join(
                f"// File: {file}\n\n{_wipe(src)}" for src, file in zip(sources, flattened_deps)
            )
        )

        # hopefully this doesn't mess up anything pretty, but just gotta remove all
        # that extraneous whitespace
        return _sub(r"\n{3,}", "\n\n", flat)

    @property
    def standard_input_json(self) -> Dict:
        """Useful for etherscan verification via solidity-standard-json-input mode.

        Sadly programmatic upload of this isn't available at the moment (2021-10-11)
        """
        return {
            "language": "Solidity",
            "sources": {k: {"content": v} for k, v in self.sources.items()},
            "settings": self.compiler_settings,
        }

    def remap_import(self, import_path: str) -> str:
        """Remap imports in a solidity source file.

        Args:
            import_path: The path component of an import directive from a solidity source file.

        Returns:
            str: The import path string correctly remapped.
        """
        for k, v in self.remappings.items():
            if import_path.startswith(k):
                return import_path.replace(k, v, 1)
        return import_path

    @staticmethod
    def make_import_absolute(import_path: str, source_file_dir: str) -> str:
        """Make an import path absolute, if it is not already.

        Args:
            source_file_dir: The parent directory of the source file where the import path appears.
            import_path: The path component of an import directive (should already remapped).

        Returns:
            str: The import path string in absolute form.
        """
        path = _Path(import_path)
        if path.is_absolute():
            return path.as_posix()

        dir_path = _Path(source_file_dir).resolve()
        newpath = (dir_path / path).resolve()
        while not newpath.exists():
            dir_path = dir_path.parent
            newpath = (dir_path / path).resolve()
            if dir_path == _Path("/"):
                raise FileNotFoundError(f"Cannot determine location of {import_path}")
        return newpath.as_posix()


def _wipe(src: str) -> str:
    """go through and remove all imports/pragmas/license stuff."""
    return _PRAGMA_PATTERN_SUB("", _LICENSE_PATTERN_SUB("", _IMPORT_PATTERN_SUB("", src)))


# Internal C Constants

_IMPORT_PATTERN_FINDITER: Final = IMPORT_PATTERN.finditer
_IMPORT_PATTERN_SUB: Final = IMPORT_PATTERN.sub

_PRAGMA_PATTERN_FINDALL: Final = PRAGMA_PATTERN.findall
_PRAGMA_PATTERN_SUB: Final = PRAGMA_PATTERN.sub

_LICENSE_PATTERN_SEARCH: Final = LICENSE_PATTERN.search
_LICENSE_PATTERN_SUB: Final = LICENSE_PATTERN.sub
