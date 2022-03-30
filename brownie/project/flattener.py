import re
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, Set

from eth_hash.auto import keccak

from brownie._config import _load_project_structure_config
from brownie.utils.toposort import toposort_flatten

# Patten matching Solidity `import-directive`, capturing path component
# https://docs.soliditylang.org/en/latest/grammar.html#a4.SolidityParser.importDirective
IMPORT_PATTERN = re.compile(
    r"^[ \t\r\f\v]*import\s+[^'\"]*['\"](?P<path>.+)['\"][^;]*;", re.MULTILINE
)
PRAGMA_PATTERN = re.compile(r"^pragma.*;$", re.MULTILINE)
LICENSE_PATTERN = re.compile(r"^// SPDX-License-Identifier: (.*)$", re.MULTILINE)


class SourceKeyCollision(Exception):
    pass


class Flattener:
    """Brownie's Robust Solidity Flattener."""

    def __init__(
        self, primary_source_fp: str, contract_name: str, remappings: dict, compiler_settings: dict
    ) -> None:
        self.sources: Dict[str, str] = {}
        self.dependencies: DefaultDict[str, Set[str]] = defaultdict(set)
        self.compiler_settings = compiler_settings
        self.contract_name = contract_name
        self.contract_file = Path(primary_source_fp).name
        self.remappings = remappings

        self._libraries = compiler_settings.get("libraries", {})

        self._contracts_dir = (
            Path(".").joinpath(_load_project_structure_config(Path("."))["contracts"]).resolve()
        )

        self.traverse(primary_source_fp)

        license_search = LICENSE_PATTERN.search(
            self.sources[self._get_primary_source_key(Path(primary_source_fp))]
        )
        self.license = license_search.group(1) if license_search else "NONE"

    def _is_sources_collision(self, key: str, new_source: str) -> bool:
        """Check if try to set `self.sources[key]` with different content
        In such case some files will be missed
        """
        return keccak(self.sources.get(key, "").encode("utf-8")) != keccak(
            new_source.encode("utf-8")
        )

    def _prepare_key_for_sources(self, source_file_path: str) -> str:
        """Prepare key for `self.sources` dict"""
        for key, value in self.remappings.items():
            if source_file_path.startswith(value):
                return Path(key).joinpath(Path(source_file_path).relative_to(value)).as_posix()
        return self._get_primary_source_key(Path(source_file_path))

    def _get_primary_source_key(self, primary_source_path: Path) -> str:
        return primary_source_path.resolve().relative_to(self._contracts_dir).as_posix()

    def traverse(self, fp: str) -> None:
        """Traverse a contract source files dependencies.

        Files are read in, import statement path components are substituted for their absolute
        path, and the modified source is saved along with it's dependencies.

        Args:
            fp: The contract source file to traverse, if it's already been traversed, return early.
        """

        fp_obj = Path(fp)
        # read in the source file
        source = fp_obj.read_text()

        source_key = self._prepare_key_for_sources(fp_obj.as_posix())

        # if already traversed file, return early
        if source_key in self.sources:
            # check potential key name collision
            if self._is_sources_collision(source_key, source):
                raise SourceKeyCollision(f"Collision with key name '{source_key}' in {fp_obj}")
            return

        self.sources[source_key] = source

        sanitize = lambda path: self.make_import_absolute(  # noqa: E731
            self.remap_import(path), fp_obj.parent.as_posix()
        )

        if source_key not in self.dependencies:
            self.dependencies[source_key] = set()

        # traverse dependency files - can circular imports happen?
        for m in IMPORT_PATTERN.finditer(source):
            import_path = sanitize(m.group("path"))
            self.dependencies[source_key].add(self._prepare_key_for_sources(import_path))
            self.traverse(import_path)

    @property
    def flattened_source(self) -> str:
        """The flattened source code for use verifying."""
        # all source files in the correct order for concatenation
        sources = [self.sources[k] for k in toposort_flatten(self.dependencies)]
        # all pragma statements, we already have the license used + know which compiler
        # version is used via the build info
        pragmas = set((match.strip() for src in sources for match in PRAGMA_PATTERN.findall(src)))
        # now we go thorugh and remove all imports/pragmas/license stuff
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
        input_json = {
            "language": "Solidity",
            "sources": {k: {"content": v} for k, v in self.sources.items()},
            "settings": self.compiler_settings,
        }
        if self._libraries:
            input_json["settings"]["libraries"] = self._prepare_library_dict_to_json_input()  # type: ignore  # noqa

        return input_json

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

        return (Path(source_file_dir) / path).resolve().as_posix()

    def _prepare_library_dict_to_json_input(self) -> Dict[str, Dict[str, str]]:
        output_dict: dict = {}
        # find in raw string of source code
        lib = re.compile(r"[\\n]?[ ]*library[\\n ]*(?P<lib>[^\\n ]+)[\\n ]*{")
        for key, source in self.sources.items():
            for match in lib.finditer(source):
                lib_name = match.group("lib")
                if lib_name in self._libraries:
                    if key not in output_dict:
                        output_dict[key] = {lib_name: self._libraries[lib_name]}
                    else:
                        output_dict[key][lib_name] = self._libraries[lib_name]
        return output_dict
