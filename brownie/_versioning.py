#!/usr/bin/python3

import re
from collections.abc import Iterable
from typing import Any

import semantic_version
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version

# Vyper switched version pragmas from semantic_version.NpmSpec to
# packaging.specifiers.SpecifierSet in v0.3.10.
VYPER_PEP440_PRAGMA_VERSION = Version("0.3.10")


def parse_compiler_version(version: Any) -> Version:
    text = str(version).removeprefix("v")
    return Version(text.split("+", 1)[0])


def parse_compiler_versions(versions: Iterable[Any]) -> list[Version]:
    return [parse_compiler_version(version) for version in versions]


def next_minor(version: Version) -> Version:
    return Version(f"{version.major}.{version.minor + 1}.0")


def _normalize_legacy_vyper_prerelease(expression: str) -> str:
    expression = re.sub(r"(?<=\d)alpha(?=\d)", "-alpha.", expression, flags=re.I)
    expression = re.sub(r"(?<=\d)beta(?=\d)", "-beta.", expression, flags=re.I)
    expression = re.sub(r"(?<=\d)a(?=\d)", "-alpha.", expression, flags=re.I)
    expression = re.sub(r"(?<=\d)b(?=\d)", "-beta.", expression, flags=re.I)
    return re.sub(r"(?<=\d)rc(?=\d)", "-rc.", expression, flags=re.I)


def _reject_solidity_version_qualifiers(expression: str) -> None:
    # solc supports qualifiers on its own compiler version, not inside pragma
    # match expressions. Hyphen ranges remain valid because they use whitespace.
    if re.search(r"\d+(?:\.\d+){0,2}(?:-[0-9A-Za-z]|\+[0-9A-Za-z])", expression):
        raise ValueError(f"Invalid Solidity version pragma: {expression}")


def _normalize_npm_expression(expression: str) -> str:
    expression = expression.strip()
    expression = re.sub(r"""(["'])([^"']+)\1""", r"\2", expression)
    expression = re.sub(r"(<=|>=|<|>|=|\^|~)\s+(?=[v0-9xX*])", r"\1", expression)
    return re.sub(r"(?<=[0-9xX*])(?=(?:<=|>=|<|>|=|\^|~)[v0-9xX*])", " ", expression)


def _normalize_solidity_npm_expression(expression: str) -> str:
    expression = _normalize_npm_expression(expression)
    # solc treats ^0.0.patch as >=0.0.patch,<0.1.0, while NpmSpec uses
    # npm's narrower >=0.0.patch,<0.0.(patch+1) range.
    return re.sub(r"(?<!\S)\^0\.0\.(\d+)(?!\S)", r">=0.0.\1 <0.1.0", expression)


def _to_semantic_version(version: Any) -> semantic_version.Version:
    version = parse_compiler_version(version)
    prerelease = ""
    if version.pre:
        phase, number = version.pre
        prerelease_phase = {"a": "alpha", "b": "beta"}.get(phase, phase)
        prerelease = f"-{prerelease_phase}.{number}"
    return semantic_version.Version(f"{version.major}.{version.minor}.{version.micro}{prerelease}")


def _reject_solidity_npm_expression(expression: str) -> None:
    for token in re.findall(r"(?<![0-9A-Za-z_.-])v\d+(?:\.\d+){0,2}", expression):
        raise ValueError(f"Invalid Solidity version pragma: {token}")


class _NpmSpec:
    def __init__(self, expression: str, *, normalize_legacy_vyper: bool = False) -> None:
        self.expression = expression
        if normalize_legacy_vyper:
            expression = _normalize_legacy_vyper_prerelease(expression)
        try:
            self._spec = semantic_version.NpmSpec(_normalize_npm_expression(expression))
        except Exception:
            raise ValueError(f"Invalid npm version range: {expression}")

    def __contains__(self, version: Any) -> bool:
        return self._spec.match(_to_semantic_version(version))


class SolidityPragmaSpec:
    """Solidity pragma matcher with solc-style multiple-pragma intersection."""

    def __init__(self, expressions: str | Iterable[str]) -> None:
        if isinstance(expressions, str):
            expressions = [expressions]

        self.expressions = tuple(expressions)
        if not self.expressions:
            raise ValueError("No Solidity version pragma")

        for expression in self.expressions:
            _reject_solidity_version_qualifiers(expression)
            _reject_solidity_npm_expression(expression)
        try:
            self._ranges = tuple(
                _NpmSpec(_normalize_solidity_npm_expression(expression))
                for expression in self.expressions
            )
        except Exception:
            raise ValueError(f"Invalid Solidity version pragma: {self}")

    def __contains__(self, version: Any) -> bool:
        version = parse_compiler_version(version)
        return all(version in range_spec for range_spec in self._ranges)

    def select(self, versions: Iterable[Any]) -> Version | None:
        return max(
            (parse_compiler_version(version) for version in versions if version in self),
            default=None,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SolidityPragmaSpec) and self.expressions == other.expressions

    def __str__(self) -> str:
        return " && ".join(self.expressions)

    def __repr__(self) -> str:
        return f"SolidityPragmaSpec({self.expressions!r})"


def _to_vyper_modern_expression(expression: str) -> str:
    if re.match("[v0-9]", expression):
        expression = f"=={expression}"
    return re.sub(r"^\^", "~=", expression)


class _VyperLegacySpec:
    def __init__(self, expression: str) -> None:
        try:
            self._spec = _NpmSpec(expression, normalize_legacy_vyper=True)
        except Exception:
            raise ValueError(f"Invalid Vyper version pragma: {expression}")

    def __contains__(self, version: Any) -> bool:
        return version in self._spec


def _to_vyper_legacy_spec(expression: str) -> _VyperLegacySpec:
    try:
        return _VyperLegacySpec(expression)
    except Exception:
        raise ValueError(f"Invalid Vyper version pragma: {expression}")


class VyperPragmaSpec:
    """Vyper pragma matcher with modern PEP440 and legacy @version support."""

    def __init__(self, expression: str, allow_legacy: bool = False) -> None:
        self.expression = expression
        self.allow_legacy = allow_legacy

        try:
            self._modern_spec: SpecifierSet | None = SpecifierSet(
                _to_vyper_modern_expression(expression)
            )
        except InvalidSpecifier:
            self._modern_spec = None

        try:
            self._legacy_spec: _VyperLegacySpec | None = _to_vyper_legacy_spec(expression)
        except Exception:
            self._legacy_spec = None

        if self._modern_spec is None and (not allow_legacy or self._legacy_spec is None):
            raise ValueError(f"Invalid Vyper version pragma: {expression}")

    def __contains__(self, version: Any) -> bool:
        version = parse_compiler_version(version)

        if version >= VYPER_PEP440_PRAGMA_VERSION:
            if self._modern_spec is None:
                return False
            return self._modern_spec.contains(version, prereleases=True)

        if self.allow_legacy and self._legacy_spec is not None:
            return version in self._legacy_spec

        return False

    def select(self, versions: Iterable[Any]) -> Version | None:
        return max(
            (parse_compiler_version(version) for version in versions if version in self),
            default=None,
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, VyperPragmaSpec):
            return self.expression == other.expression and self.allow_legacy == other.allow_legacy
        return False

    def __str__(self) -> str:
        return self.expression

    def __repr__(self) -> str:
        return f"VyperPragmaSpec({self.expression!r}, allow_legacy={self.allow_legacy!r})"
