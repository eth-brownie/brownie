import re
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, Set

from brownie.utils.toposort import toposort_flatten

# Patten matching Solidity `import-directive`, capturing path component
# https://docs.soliditylang.org/en/latest/grammar.html#a4.SolidityParser.importDirective
IMPORT_PATTERN = re.compile(
    r"(?<=\n)?import(?P<prefix>.*)(?P<quote>[\"'])(?P<path>.*)(?P=quote)(?P<suffix>.*)(?=\n)"
)
PRAGMA_PATTERN = re.compile(r"^pragma.*;$", re.MULTILINE)
LICENSE_PATTERN = re.compile(r"^// SPDX-License-Identifier: (.*)$", re.MULTILINE)


class Flattener:
    """Brownie's Robust Solidity Flattener."""

    def __init__(
        self, primary_source_fp: str, contract_name: str, remappings: dict, compiler_settings: dict
    ) -> None:
        self.sources: Dict[str, str] = {}
        self.dependencies: DefaultDict[str, Set[str]] = defaultdict(set)
        self.compiler_settings = compiler_settings
        self.contract_name = contract_name
        self.contract_file = self.path_to_name(primary_source_fp)
        self.remappings = remappings

        self.traverse(primary_source_fp)

        license_search = LICENSE_PATTERN.search(self.path_to_name(primary_source_fp))
        self.license = license_search.group(1) if license_search else "NONE"

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
        fp_obj = Path(fp)
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
        self.sources[name] = IMPORT_PATTERN.sub(repl, source)
        if fp_obj.name not in self.dependencies:
            self.dependencies[name] = set()

        # traverse dependency files - can circular imports happen?
        for m in IMPORT_PATTERN.finditer(source):
            import_path = sanitize(m.group("path"))
            self.dependencies[name].add(self.path_to_name(import_path))
            self.traverse(import_path)

    @property
    def flattened_source(self) -> str:
        """The flattened source code for use verifying."""
        # all source files in the correct order for concatenation
        sources = [self.sources[k] for k in toposort_flatten(self.dependencies)]
        # all pragma statements, we already have the license used + know which compiler
        # version is used via the build info
        pragmas = set((match.strip() for src in sources for match in PRAGMA_PATTERN.findall(src)))
        # now we go through and remove all imports/pragmas/license stuff
        wipe = lambda src: PRAGMA_PATTERN.sub(  # noqa: E731
            "", LICENSE_PATTERN.sub("", IMPORT_PATTERN.sub("", src))
        )

        sources = [
            f"// File: {file}\n\n{wipe(src)}"
            for src, file in zip(sources, toposort_flatten(self.dependencies))
        ]

        flat = (
            "\n".join([pragma for pragma in pragmas if "pragma solidity" not in pragma])
            + "\n\n"
            + "\n".join(sources)
        )
        # hopefully this doesn't mess up anything pretty, but just gotta remove all
        # that extraneous whitespace
        return re.sub(r"\n{3,}", "\n\n", flat)

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
        path: Path = Path(import_path)
        if path.is_absolute():
            return path.as_posix()

        source_file_dir = Path(source_file_dir).resolve()
        newpath = (source_file_dir / path).resolve()
        while not newpath.exists():
            source_file_dir = source_file_dir.parent
            newpath = (source_file_dir / path).resolve()
            if source_file_dir == Path("/"):
                raise FileNotFoundError(f"Cannot determine location of {import_path}")
        return newpath.as_posix()
