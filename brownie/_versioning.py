#!/usr/bin/python3

import re
from collections.abc import Callable, Iterable
from typing import Any

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version
from vvm.utils.convert import to_vyper_version

# Vyper switched version pragmas from semantic_version.NpmSpec to
# packaging.specifiers.SpecifierSet in v0.3.10.
VYPER_PEP440_PRAGMA_VERSION = Version("0.3.10")


def parse_compiler_version(version: Any) -> Version:
    text = str(version).lstrip("v")
    return Version(text.split("+", 1)[0])


def parse_compiler_versions(versions: Iterable[Any]) -> list[Version]:
    return [parse_compiler_version(version) for version in versions]


def next_minor(version: Version) -> Version:
    return Version(f"{version.major}.{version.minor + 1}.0")


def _normalize_legacy_vyper_prerelease(expression: str) -> str:
    expression = re.sub(r"(?<=\d)a(?=\d)", "-alpha.", expression)
    expression = re.sub(r"(?<=\d)b(?=\d)", "-beta.", expression)
    return re.sub(r"(?<=\d)rc(?=\d)", "-rc.", expression)


def _reject_solidity_version_qualifiers(expression: str) -> None:
    # solc supports qualifiers on its own compiler version, not inside pragma
    # match expressions. Hyphen ranges remain valid because they use whitespace.
    if re.search(r"\d+(?:\.\d+){0,2}(?:-[0-9A-Za-z]|\+[0-9A-Za-z])", expression):
        raise ValueError(f"Invalid Solidity version pragma: {expression}")


def _parse_semver_version(
    value: str, allow_prerelease_match: bool = False
) -> tuple[Version, Version | None]:
    value = value.lstrip("v")
    if value in {"*", "x", "X"}:
        return Version("0.0.0"), None

    suffix = ""
    if "-" in value:
        value, suffix = value.split("-", 1)
        if not allow_prerelease_match:
            raise ValueError(f"Invalid semantic version: {value}-{suffix}")
    if "+" in value:
        raise ValueError(f"Invalid semantic version: {value}")

    parts = value.split(".")
    if not 1 <= len(parts) <= 3:
        raise ValueError(f"Invalid semantic version: {value}")

    numeric: list[int] = []
    wildcard_index: int | None = None
    for idx, part in enumerate(parts):
        if part in {"*", "x", "X"}:
            if suffix:
                raise ValueError(f"Invalid semantic version: {value}-{suffix}")
            wildcard_index = idx
            numeric.append(0)
            break
        numeric.append(int(part))

    if wildcard_index is None and len(parts) < 3:
        wildcard_index = len(parts)

    while len(numeric) < 3:
        numeric.append(0)

    lower_text = ".".join(str(i) for i in numeric[:3])
    lower = Version(f"{lower_text}-{suffix}" if suffix else lower_text)
    if wildcard_index is None:
        return lower, None

    if wildcard_index == 0:
        return lower, None
    if wildcard_index == 1:
        return lower, Version(f"{numeric[0] + 1}.0.0")
    return lower, Version(f"{numeric[0]}.{numeric[1] + 1}.0")


def _caret_upper_bound(lower: Version, expression: str) -> Version:
    if lower.major or len(expression.lstrip("v").split(".")) == 1:
        return Version(f"{lower.major + 1}.0.0")
    return Version(f"0.{lower.minor + 1}.0")


def _npm_caret_upper_bound(lower: Version) -> Version:
    if lower.major:
        return Version(f"{lower.major + 1}.0.0")
    if lower.minor:
        return Version(f"0.{lower.minor + 1}.0")
    return Version(f"0.0.{lower.micro + 1}")


def _tilde_upper_bound(lower: Version, expression: str) -> Version:
    parts = expression.lstrip("v").split(".")
    if len(parts) == 1:
        return Version(f"{lower.major + 1}.0.0")
    return Version(f"{lower.major}.{lower.minor + 1}.0")


def _hyphen_replacement(match: re.Match) -> str:
    return f">={match.group(1)} <={match.group(2)}"


def _expand_hyphen_ranges(expression: str) -> str:
    matches = list(re.finditer(r"(\S+)\s+-\s+(\S+)", expression))
    if not matches:
        return expression
    if len(matches) > 1 or expression.strip() != matches[0].group(0):
        raise ValueError(f"Invalid semantic version range: {expression}")
    return _hyphen_replacement(matches[0])


def _predicate_for_token(
    token: str, npm_caret: bool = False, allow_prerelease_match: bool = False
) -> Callable[[Version], bool]:
    match = re.fullmatch(r"(<=|>=|<|>|=|\^|~)?(.+)", token)
    if match is None:
        raise ValueError(f"Invalid Solidity version pragma token: {token}")

    operator = match.group(1) or ""
    value = match.group(2)
    lower, upper = _parse_semver_version(value, allow_prerelease_match)

    if operator in {"", "="}:
        if upper is not None:
            return lambda version: lower <= version < upper
        return lambda version: version == lower
    if operator == ">=":
        return lambda version: version >= lower
    if operator == ">":
        if upper is not None:
            return lambda version: version >= upper
        return lambda version: version > lower
    if operator == "<=":
        if upper is not None:
            return lambda version: version < upper
        return lambda version: version <= lower
    if operator == "<":
        return lambda version: version < lower
    if operator == "^":
        upper = _npm_caret_upper_bound(lower) if npm_caret else _caret_upper_bound(lower, value)
        return lambda version: lower <= version < upper
    if operator == "~":
        return lambda version: lower <= version < _tilde_upper_bound(lower, value)

    raise ValueError(f"Invalid Solidity version pragma token: {token}")


def _compile_semver_branch(
    expression: str, npm_caret: bool = False, allow_prerelease_match: bool = False
) -> Callable[[Version], bool]:
    expression = re.sub(r"(<=|>=|<|>|=|\^|~)\s+(?=[0-9xX*])", r"\1", expression)
    tokens = _expand_hyphen_ranges(expression).split()
    if not tokens:
        raise ValueError("Invalid empty semantic version expression")
    predicates = [
        _predicate_for_token(token, npm_caret, allow_prerelease_match) for token in tokens
    ]
    return lambda version: all(predicate(version) for predicate in predicates)


class _SemverRangeSpec:
    def __init__(
        self,
        expression: str,
        npm_caret: bool = False,
        allow_prerelease_match: bool = False,
    ) -> None:
        self.expression = expression
        self._branches = tuple(
            _compile_semver_branch(branch.strip(), npm_caret, allow_prerelease_match)
            for branch in expression.split("||")
        )

    def __contains__(self, version: Any) -> bool:
        version = parse_compiler_version(version)
        return any(branch(version) for branch in self._branches)


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
        self._ranges = tuple(_SemverRangeSpec(expression) for expression in self.expressions)

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
        self._specs: list[SpecifierSet | _SemverRangeSpec] = []
        expression = _normalize_legacy_vyper_prerelease(expression)

        try:
            version = parse_compiler_version(to_vyper_version(expression))
            self._specs.append(SpecifierSet(f"=={version}"))
        except Exception:
            pass

        try:
            self._specs.append(
                _SemverRangeSpec(expression, npm_caret=True, allow_prerelease_match=True)
            )
        except Exception:
            pass

        if not self._specs:
            raise ValueError(f"Invalid Vyper version pragma: {expression}")

    def __contains__(self, version: Any) -> bool:
        version = parse_compiler_version(version)
        return any(
            (
                spec.contains(version, prereleases=True)
                if isinstance(spec, SpecifierSet)
                else version in spec
            )
            for spec in self._specs
        )


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
