#!/usr/bin/python3

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version
from vvm.utils.convert import to_vyper_version

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
    expression = re.sub(r"(?<=\d)a(?=\d)", "-alpha.", expression)
    expression = re.sub(r"(?<=\d)b(?=\d)", "-beta.", expression)
    return re.sub(r"(?<=\d)rc(?=\d)", "-rc.", expression)


def _reject_solidity_version_qualifiers(expression: str) -> None:
    # solc supports qualifiers on its own compiler version, not inside pragma
    # match expressions. Hyphen ranges remain valid because they use whitespace.
    if re.search(r"\d+(?:\.\d+){0,2}(?:-[0-9A-Za-z]|\+[0-9A-Za-z])", expression):
        raise ValueError(f"Invalid Solidity version pragma: {expression}")


@dataclass(frozen=True)
class _SemverPattern:
    numbers: tuple[int | None, int | None, int | None]
    levels_present: int
    suffix: str = ""

    @property
    def version(self) -> Version:
        text = ".".join(str(i or 0) for i in self.numbers)
        return Version(f"{text}-{self.suffix}" if self.suffix else text)

    @property
    def has_prerelease(self) -> bool:
        return bool(self.suffix)

    @property
    def has_wildcard(self) -> bool:
        return any(i is None for i in self.numbers[: self.levels_present])


def _parse_semver_pattern(value: str, allow_prerelease_match: bool = False) -> _SemverPattern:
    if value.startswith("v"):
        raise ValueError(f"Invalid semantic version: {value}")

    if value in {"*", "x", "X"}:
        return _SemverPattern((None, 0, 0), 1)

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

    numeric: list[int | None] = []
    levels_present = len(parts)
    for idx, part in enumerate(parts):
        if part in {"*", "x", "X"}:
            if suffix:
                raise ValueError(f"Invalid semantic version: {value}-{suffix}")
            numeric.append(None)
            continue
        if not re.fullmatch(r"0|[1-9][0-9]*", part):
            raise ValueError(f"Invalid semantic version: {value}")
        numeric.append(int(part))

    while len(numeric) < 3:
        numeric.append(0)

    return _SemverPattern(tuple(numeric[:3]), levels_present, suffix)


def _compare_semver_pattern(version: Version, pattern: _SemverPattern) -> tuple[int, bool]:
    candidate = (version.major, version.minor, version.micro)
    did_compare = False

    for idx in range(pattern.levels_present):
        expected = pattern.numbers[idx]
        if expected is None:
            continue
        did_compare = True
        if candidate[idx] != expected:
            return candidate[idx] - expected, did_compare

    if version.is_prerelease and did_compare:
        return -1, did_compare
    return 0, did_compare


def _next_patch(version: Version) -> Version:
    return Version(f"{version.major}.{version.minor}.{version.micro + 1}")


def _npm_caret_upper_bound(pattern: _SemverPattern) -> Version:
    lower = pattern.version
    if lower.major:
        return Version(f"{lower.major + 1}.0.0")
    if lower.minor:
        return Version(f"0.{lower.minor + 1}.0")
    return Version(f"0.0.{lower.micro + 1}")


def _solc_tilde_upper_pattern(pattern: _SemverPattern) -> _SemverPattern:
    levels_present = 2 if pattern.levels_present >= 2 else 1
    return _SemverPattern(pattern.numbers, levels_present)


def _solc_caret_upper_pattern(pattern: _SemverPattern) -> _SemverPattern:
    levels_present = 2 if pattern.numbers[0] == 0 and pattern.levels_present != 1 else 1
    return _SemverPattern(pattern.numbers, levels_present)


def _matches_pattern_operator(version: Version, operator: str, pattern: _SemverPattern) -> bool:
    if pattern.has_prerelease and not pattern.has_wildcard:
        lower = pattern.version
        if operator in {"", "="}:
            return version == lower
        if operator == ">=":
            return version >= lower
        if operator == ">":
            return version > lower
        if operator == "<=":
            return version <= lower
        if operator == "<":
            return version < lower

    cmp, _ = _compare_semver_pattern(version, pattern)
    if operator in {"", "="}:
        return cmp == 0
    if operator == ">=":
        return cmp >= 0
    if operator == ">":
        return cmp > 0
    if operator == "<=":
        return cmp <= 0
    if operator == "<":
        return cmp < 0
    raise ValueError(f"Invalid semantic version operator: {operator}")


def _hyphen_replacement(match: re.Match) -> str:
    return f">={match.group(1)} <={match.group(2)}"


def _expand_hyphen_ranges(expression: str) -> str:
    matches = list(re.finditer(r"(\S+)\s+-\s+(\S+)", expression))
    if not matches:
        return expression
    if len(matches) > 1 or expression.strip() != matches[0].group(0):
        raise ValueError(f"Invalid semantic version range: {expression}")
    return _hyphen_replacement(matches[0])


def _predicate_for_token(token: str) -> Callable[[Version], bool]:
    match = re.fullmatch(r"(<=|>=|<|>|=|\^|~)?(.+)", token)
    if match is None:
        raise ValueError(f"Invalid Solidity version pragma token: {token}")

    operator = match.group(1) or ""
    value = match.group(2)
    pattern = _parse_semver_pattern(value)

    if operator in {"", "=", ">=", ">", "<=", "<"}:
        return lambda version: _matches_pattern_operator(version, operator, pattern)
    if operator == "^":
        upper_pattern = _solc_caret_upper_pattern(pattern)
        return lambda version: _matches_pattern_operator(
            version, ">=", pattern
        ) and _matches_pattern_operator(version, "<=", upper_pattern)
    if operator == "~":
        upper_pattern = _solc_tilde_upper_pattern(pattern)
        return lambda version: _matches_pattern_operator(
            version, ">=", pattern
        ) and _matches_pattern_operator(version, "<=", upper_pattern)

    raise ValueError(f"Invalid Solidity version pragma token: {token}")


def _compile_semver_branch(expression: str) -> Callable[[Version], bool]:
    expression = re.sub(r"(<=|>=|<|>|=|\^|~)\s+(?=[0-9xX*])", r"\1", expression)
    tokens = _expand_hyphen_ranges(expression).split()
    if not tokens:
        raise ValueError("Invalid empty semantic version expression")
    predicates = [_predicate_for_token(token) for token in tokens]
    return lambda version: all(predicate(version) for predicate in predicates)


class _SemverRangeSpec:
    def __init__(self, expression: str) -> None:
        self.expression = expression
        self._branches = tuple(
            _compile_semver_branch(branch.strip()) for branch in expression.split("||")
        )

    def __contains__(self, version: Any) -> bool:
        version = parse_compiler_version(version)
        return any(branch(version) for branch in self._branches)


def _npm_release_tuple(version: Version) -> tuple[int, int, int]:
    return version.major, version.minor, version.micro


def _npm_lower_from_pattern(pattern: _SemverPattern) -> Version:
    numbers = list(pattern.numbers)
    for idx in range(pattern.levels_present):
        if numbers[idx] is None:
            numbers[idx:] = [0] * (3 - idx)
            break
    return Version(".".join(str(i or 0) for i in numbers))


def _npm_xrange_upper_bound(pattern: _SemverPattern) -> Version | None:
    numbers = pattern.numbers
    for idx in range(pattern.levels_present):
        if numbers[idx] is None:
            if idx == 0:
                return None
            if idx == 1:
                return Version(f"{numbers[0] + 1}.0.0")  # type: ignore [operator]
            return Version(f"{numbers[0]}.{numbers[1] + 1}.0")  # type: ignore [operator]

    if pattern.levels_present == 1:
        return Version(f"{numbers[0] + 1}.0.0")  # type: ignore [operator]
    if pattern.levels_present == 2:
        return Version(f"{numbers[0]}.{numbers[1] + 1}.0")  # type: ignore [operator]
    return _next_patch(pattern.version)


def _npm_tilde_upper_bound(pattern: _SemverPattern) -> Version:
    lower = pattern.version
    if pattern.has_prerelease:
        return _next_patch(lower)
    if pattern.levels_present == 1:
        return Version(f"{lower.major + 1}.0.0")
    return Version(f"{lower.major}.{lower.minor + 1}.0")


def _npm_base_predicate(pattern: _SemverPattern) -> Callable[[Version], bool]:
    lower = _npm_lower_from_pattern(pattern)
    upper = _npm_xrange_upper_bound(pattern)
    if upper is None:
        return lambda version: version >= lower
    return lambda version: lower <= version < upper


def _npm_predicate_for_token(
    token: str,
) -> tuple[Callable[[Version], bool], set[tuple[int, int, int]]]:
    match = re.fullmatch(r"(<=|>=|<|>|=|\^|~)?(.+)", token)
    if match is None:
        raise ValueError(f"Invalid npm version range token: {token}")

    operator = match.group(1) or ""
    pattern = _parse_semver_pattern(match.group(2), allow_prerelease_match=True)
    prerelease_bases = {_npm_release_tuple(pattern.version)} if pattern.has_prerelease else set()

    if operator in {"", "="}:
        return _npm_base_predicate(pattern), prerelease_bases
    if operator == ">=":
        lower = pattern.version
        return lambda version: version >= lower, prerelease_bases
    if operator == ">":
        lower = pattern.version
        return lambda version: version > lower, prerelease_bases
    if operator == "<=":
        if pattern.has_wildcard or pattern.levels_present < 3:
            upper = _npm_xrange_upper_bound(pattern)
            if upper is None:
                return lambda version: True, prerelease_bases
            return lambda version: version < upper, prerelease_bases
        upper = pattern.version
        return lambda version: version <= upper, prerelease_bases
    if operator == "<":
        upper = pattern.version
        return lambda version: version < upper, prerelease_bases
    if operator == "^":
        lower = pattern.version
        upper = _npm_caret_upper_bound(pattern)
        return lambda version: lower <= version < upper, prerelease_bases
    if operator == "~":
        lower = pattern.version
        upper = _npm_tilde_upper_bound(pattern)
        return lambda version: lower <= version < upper, prerelease_bases

    raise ValueError(f"Invalid npm version range operator: {operator}")


def _compile_npm_branch(expression: str) -> Callable[[Version], bool]:
    expression = re.sub(r"(<=|>=|<|>|=|\^|~)\s+(?=[0-9xX*])", r"\1", expression)
    tokens = _expand_hyphen_ranges(expression).split()
    if not tokens:
        raise ValueError("Invalid empty npm version expression")

    predicates: list[Callable[[Version], bool]] = []
    prerelease_bases: set[tuple[int, int, int]] = set()
    for token in tokens:
        predicate, token_prerelease_bases = _npm_predicate_for_token(token)
        predicates.append(predicate)
        prerelease_bases.update(token_prerelease_bases)

    def matches(version: Version) -> bool:
        if version.is_prerelease and _npm_release_tuple(version) not in prerelease_bases:
            return False
        return all(predicate(version) for predicate in predicates)

    return matches


class _NpmRangeSpec:
    def __init__(self, expression: str) -> None:
        self.expression = expression
        self._branches = tuple(
            _compile_npm_branch(branch.strip()) for branch in expression.split("||")
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
        self._specs: list[SpecifierSet | _NpmRangeSpec] = []
        expression = _normalize_legacy_vyper_prerelease(expression)

        try:
            version = parse_compiler_version(to_vyper_version(expression))
            self._specs.append(SpecifierSet(f"=={version}"))
        except Exception:
            pass

        try:
            self._specs.append(_NpmRangeSpec(expression))
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
