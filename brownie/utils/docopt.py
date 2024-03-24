"""Docopt is a Pythonic command-line interface parser that will make you smile.

Now: with spellcheck, flag extension (de-abbreviation), and capitalization fixes.
(but only when unambiguous)

 * Licensed under terms of MIT license (see LICENSE-MIT)

Contributors (roughly in chronological order):

 * Copyright (c) 2012 Andrew Kassen <atkassen@ucdavis.edu>
 * Copyright (c) 2012 jeffrimko <jeffrimko@gmail.com>
 * Copyright (c) 2012 Andrew Sutton <met48@met48.com>
 * Copyright (c) 2012 Andrew Sutton <met48@met48.com>
 * Copyright (c) 2012 Nima Johari <nimajohari@gmail.com>
 * Copyright (c) 2012-2013 Vladimir Keleshev, vladimir@keleshev.com
 * Copyright (c) 2014-2018 Matt Boersma <matt@sprout.org>
 * Copyright (c) 2016 amir <ladsgroup@gmail.com>
 * Copyright (c) 2015 Benjamin Bach <benjaoming@gmail.com>
 * Copyright (c) 2017 Oleg Bulkin <o.bulkin@gmail.com>
 * Copyright (c) 2018 Iain Barnett <iainspeed@gmail.com>
 * Copyright (c) 2019 itdaniher, itdaniher@gmail.com

"""

from __future__ import annotations

import re
import sys
from typing import Any, Callable, NamedTuple, Tuple, Type, Union, cast

__all__ = ["docopt", "DocoptExit", "ParsedOptions"]
__version__ = "0.9.0"


def levenshtein_norm(source: str, target: str) -> float:
    """Returns float in the range 0-1, with 1 meaning the biggest possible distance"""
    distance = _levenshtein(source, target)
    return distance / max(len(source), len(target))


def _levenshtein(source: str, target: str) -> int:
    """Computes the Levenshtein distances between two strings

    Uses the Wagner-Fischer algorithm
    (https://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm).
    These distances are defined recursively, since the distance between two
    strings is just the cost of adjusting the last one or two characters plus
    the distance between the prefixes that exclude these characters (e.g. the
    distance between "tester" and "tested" is 1 + the distance between "teste"
    and "teste"). The Wagner-Fischer algorithm retains this idea but eliminates
    redundant computations by storing the distances between various prefixes in
    a matrix that is filled in iteratively.
    """

    # Create matrix of correct size (this is s_len + 1 * t_len + 1 so that the
    # empty prefixes "" can also be included). The leftmost column represents
    # transforming various source prefixes into an empty string, which can
    # always be done by deleting all characters in the respective prefix, and
    # the top row represents transforming the empty string into various target
    # prefixes, which can always be done by inserting every character in the
    # respective prefix. The ternary used to build the list should ensure that
    # this row and column are now filled correctly
    s_range = range(len(source) + 1)
    t_range = range(len(target) + 1)
    matrix = [[(i if j == 0 else j) for j in t_range] for i in s_range]

    for i in s_range[1:]:
        for j in t_range[1:]:
            # Applies the recursive logic outlined above using the values
            # stored in the matrix so far. The options for the last pair of
            # characters are deletion, insertion, and substitution, which
            # amount to dropping the source character, the target character,
            # or both and then calculating the distance for the resulting
            # prefix combo. If the characters at this point are the same, the
            # situation can be thought of as a free substitution
            del_dist = matrix[i - 1][j] + 1
            ins_dist = matrix[i][j - 1] + 1
            sub_trans_cost = 0 if source[i - 1] == target[j - 1] else 1
            sub_dist = matrix[i - 1][j - 1] + sub_trans_cost

            # Choose option that produces smallest distance
            matrix[i][j] = min(del_dist, ins_dist, sub_dist)

    # At this point, the matrix is full, and the biggest prefixes are just the
    # strings themselves, so this is the desired distance
    return matrix[len(source)][len(target)]


class DocoptLanguageError(Exception):
    """Error in construction of usage-message by developer."""


class DocoptExit(SystemExit):
    """Exit in case user invoked program with incorrect arguments."""

    usage = ""

    def __init__(
        self,
        message: str = "",
        collected: list[_Pattern] | None = None,
        left: list[_Pattern] | None = None,
    ) -> None:
        self.collected = collected if collected is not None else []
        self.left = left if left is not None else []
        SystemExit.__init__(self, (message + "\n" + self.usage).strip())


class _Pattern:
    def __init__(self, name: str | None, value: list[str] | str | int | None = None) -> None:
        self._name, self.value = name, value

    @property
    def name(self) -> str | None:
        return self._name

    def __eq__(self, other) -> bool:
        return repr(self) == repr(other)

    def __hash__(self) -> int:
        return hash(repr(self))


def _transform(pattern: _BranchPattern) -> _Either:
    """Expand pattern into an (almost) equivalent one, but with single Either.

    Example: ((-a | -b) (-c | -d)) => (-a -c | -a -d | -b -c | -b -d)
    Quirks: [-a] => (-a), (-a...) => (-a -a)

    """
    result = []
    groups = [[pattern]]
    while groups:
        children = groups.pop(0)
        parents = [_Required, _NotRequired, _OptionsShortcut, _Either, _OneOrMore]
        if any(t in map(type, children) for t in parents):
            child = [c for c in children if type(c) in parents][0]
            children.remove(child)
            if type(child) is _Either:
                for c in child.children:
                    groups.append([c] + children)
            elif type(child) is _OneOrMore:
                groups.append(child.children * 2 + children)
            else:
                groups.append(child.children + children)
        else:
            result.append(children)
    return _Either(*[_Required(*e) for e in result])


_SingleMatch = Union[Tuple[int, "_LeafPattern"], Tuple[None, None]]


class _LeafPattern(_Pattern):
    """Leaf/terminal node of a pattern tree."""

    def __repr__(self) -> str:
        return "%s(%r, %r)" % (self.__class__.__name__, self.name, self.value)

    def single_match(self, left: list[_LeafPattern]) -> _SingleMatch:
        raise NotImplementedError  # pragma: no cover

    def flat(self, *types) -> list[_LeafPattern]:
        return [self] if not types or type(self) in types else []

    def match(
        self, left: list[_LeafPattern], collected: list[_Pattern] | None = None
    ) -> tuple[bool, list[_LeafPattern], list[_Pattern]]:
        collected = [] if collected is None else collected
        increment: Any | None = None
        pos, match = self.single_match(left)
        if match is None or pos is None:
            return False, left, collected
        left_ = left[:pos] + left[(pos + 1) :]
        same_name = [a for a in collected if a.name == self.name]
        if isinstance(self.value, int) and len(same_name) > 0:
            if isinstance(same_name[0].value, int):
                same_name[0].value += 1
            return True, left_, collected
        if isinstance(self.value, int) and not same_name:
            match.value = 1
            return True, left_, collected + [match]
        if same_name and isinstance(self.value, list):
            if isinstance(match.value, str):
                increment = [match.value]
            if same_name[0].value is not None and increment is not None:
                if isinstance(same_name[0].value, type(increment)):
                    same_name[0].value += increment
            return True, left_, collected
        elif not same_name and isinstance(self.value, list):
            if isinstance(match.value, str):
                match.value = [match.value]
            return True, left_, collected + [match]
        return True, left_, collected + [match]


class _BranchPattern(_Pattern):
    """Branch/inner node of a pattern tree."""

    def __init__(self, *children) -> None:
        self.children = list(children)

    def match(self, left: list[_Pattern], collected: list[_Pattern] | None = None) -> Any:
        raise NotImplementedError  # pragma: no cover

    def fix(self) -> _BranchPattern:
        self.fix_identities()
        self.fix_repeating_arguments()
        return self

    def fix_identities(self, uniq: list | None = None) -> None:
        """Make pattern-tree tips point to same object if they are equal."""
        flattened = self.flat()
        uniq = list(set(flattened)) if uniq is None else uniq
        for i, child in enumerate(self.children):
            if not hasattr(child, "children"):
                assert child in uniq
                self.children[i] = uniq[uniq.index(child)]
            else:
                child.fix_identities(uniq)
        return None

    def fix_repeating_arguments(self) -> _BranchPattern:
        """Fix elements that should accumulate/increment values."""
        either = [list(child.children) for child in _transform(self).children]
        for case in either:
            for e in [child for child in case if case.count(child) > 1]:
                if type(e) is _Argument or type(e) is _Option and e.argcount:
                    if e.value is None:
                        e.value = []
                    elif type(e.value) is not list:
                        e.value = cast(str, e.value)
                        e.value = e.value.split()
                if type(e) is _Command or type(e) is _Option and e.argcount == 0:
                    e.value = 0
        return self

    def __repr__(self) -> str:
        return "%s(%s)" % (
            self.__class__.__name__,
            ", ".join(repr(a) for a in self.children),
        )

    def flat(self, *types) -> Any:
        if type(self) in types:
            return [self]
        return sum([child.flat(*types) for child in self.children], [])


class _Argument(_LeafPattern):
    def single_match(self, left: list[_LeafPattern]) -> _SingleMatch:
        for n, pattern in enumerate(left):
            if type(pattern) is _Argument:
                return n, _Argument(self.name, pattern.value)
        return None, None


class _Command(_Argument):
    def __init__(self, name: str | None, value: bool = False) -> None:
        self._name, self.value = name, value

    def single_match(self, left: list[_LeafPattern]) -> _SingleMatch:
        for n, pattern in enumerate(left):
            if type(pattern) is _Argument:
                if pattern.value == self.name:
                    return n, _Command(self.name, True)
                else:
                    break
        return None, None


class _Option(_LeafPattern):
    def __init__(
        self,
        short: str | None = None,
        longer: str | None = None,
        argcount: int = 0,
        value: list[str] | str | int | None = False,
    ) -> None:
        assert argcount in (0, 1)
        self.short, self.longer, self.argcount = short, longer, argcount
        self.value = None if value is False and argcount else value

    @classmethod
    def parse(cls, option_description: str) -> _Option:
        short, longer, argcount, value = None, None, 0, False
        options, description = re.split(
            r"(?:  )|$", option_description.strip(), flags=re.M, maxsplit=1
        )
        options = options.replace(",", " ").replace("=", " ")
        for s in options.split():
            if s.startswith("--"):
                longer = s
            elif s.startswith("-"):
                short = s
            else:
                argcount = 1
        if argcount:
            matched = re.findall(r"\[default: (.*)\]", description, flags=re.I)
            value = matched[0] if matched else None
        return cls(short, longer, argcount, value)

    def single_match(self, left: list[_LeafPattern]) -> _SingleMatch:
        for n, pattern in enumerate(left):
            if self.name == pattern.name:
                return n, pattern
        return None, None

    @property
    def name(self) -> str | None:
        return self.longer or self.short

    def __repr__(self) -> str:
        return "Option(%r, %r, %r, %r)" % (
            self.short,
            self.longer,
            self.argcount,
            self.value,
        )


class _Required(_BranchPattern):
    def match(self, left: list[_Pattern], collected: list[_Pattern] | None = None) -> Any:
        collected = [] if collected is None else collected
        original_collected = collected
        original_left = left
        for pattern in self.children:
            matched, left, collected = pattern.match(left, collected)
            if not matched:
                return False, original_left, original_collected
        return True, left, collected


class _NotRequired(_BranchPattern):
    def match(self, left: list[_Pattern], collected: list[_Pattern] | None = None) -> Any:
        collected = [] if collected is None else collected
        for pattern in self.children:
            _, left, collected = pattern.match(left, collected)
        return True, left, collected


class _OptionsShortcut(_NotRequired):
    """Marker/placeholder for [options] shortcut."""


class _OneOrMore(_BranchPattern):
    def match(self, left: list[_Pattern], collected: list[_Pattern] | None = None) -> Any:
        assert len(self.children) == 1
        collected = [] if collected is None else collected
        original_collected = collected
        original_left = left
        last_left = None
        matched = True
        times = 0
        while matched:
            matched, left, collected = self.children[0].match(left, collected)
            times += 1 if matched else 0
            if last_left == left:
                break
            last_left = left
        if times >= 1:
            return True, left, collected
        return False, original_left, original_collected


class _Either(_BranchPattern):
    def match(self, left: list[_Pattern], collected: list[_Pattern] | None = None) -> Any:
        collected = [] if collected is None else collected
        outcomes = []
        for pattern in self.children:
            matched, _, _ = outcome = pattern.match(left, collected)
            if matched:
                outcomes.append(outcome)
        if outcomes:
            return min(outcomes, key=lambda outcome: len(outcome[1]))
        return False, left, collected


class _Tokens(list):
    def __init__(
        self,
        source: list[str] | str,
        error: Type[DocoptExit] | Type[DocoptLanguageError] = DocoptExit,
    ) -> None:
        if isinstance(source, list):
            self += source
        else:
            self += source.split()
        self.error = error

    @staticmethod
    def from_pattern(source: str) -> _Tokens:
        source = re.sub(r"([\[\]\(\)\|]|\.\.\.)", r" \1 ", source)
        fragments = [s for s in re.split(r"\s+|(\S*<.*?>)", source) if s]
        return _Tokens(fragments, error=DocoptLanguageError)

    def move(self) -> str | None:
        return self.pop(0) if len(self) else None

    def current(self) -> str | None:
        return self[0] if len(self) else None


def _parse_longer(
    tokens: _Tokens,
    options: list[_Option],
    argv: bool = False,
    more_magic: bool = False,
) -> list[_Pattern]:
    """longer ::= '--' chars [ ( ' ' | '=' ) chars ] ;"""
    current_token = tokens.move()
    if current_token is None or not current_token.startswith("--"):
        raise ValueError(f"parse_longer got what appears to be an invalid token: {current_token}")
    longer, maybe_eq, maybe_value = current_token.partition("=")
    if maybe_eq == maybe_value == "":
        value = None
    else:
        value = maybe_value
    similar = [o for o in options if o.longer and longer == o.longer]
    start_collision = (
        len([o for o in options if o.longer and longer in o.longer and o.longer.startswith(longer)])
        > 1
    )
    if argv and not len(similar) and not start_collision:
        similar = [
            o for o in options if o.longer and longer in o.longer and o.longer.startswith(longer)
        ]
    # try advanced matching
    if more_magic and not similar:
        corrected = [
            (longer, o) for o in options if o.longer and levenshtein_norm(longer, o.longer) < 0.25
        ]
        if corrected:
            print(f"NB: Corrected {corrected[0][0]} to {corrected[0][1].longer}")
        similar = [correct for (original, correct) in corrected]
    if len(similar) > 1:
        raise DocoptLanguageError(f"{longer} is not a unique prefix: {similar}?")
    elif len(similar) < 1:
        argcount = 1 if maybe_eq == "=" else 0
        o = _Option(None, longer, argcount)
        options.append(o)
        if tokens.error is DocoptExit:
            o = _Option(None, longer, argcount, value if argcount else True)
    else:
        o = _Option(similar[0].short, similar[0].longer, similar[0].argcount, similar[0].value)
        if o.argcount == 0:
            if value is not None:
                raise tokens.error("%s must not have an argument" % o.longer)
        else:
            if value is None:
                if tokens.current() in [None, "--"]:
                    raise tokens.error("%s requires argument" % o.longer)
                value = tokens.move()
        if tokens.error is DocoptExit:
            o.value = value if value is not None else True
    return [o]


def _parse_shorts(
    tokens: _Tokens, options: list[_Option], more_magic: bool = False
) -> list[_Pattern]:
    """shorts ::= '-' ( chars )* [ [ ' ' ] chars ] ;"""
    token = tokens.move()
    if token is None or not token.startswith("-") or token.startswith("--"):
        raise ValueError(f"parse_shorts got what appears to be an invalid token: {token}")
    left = token.lstrip("-")
    parsed: list[_Pattern] = []
    while left != "":
        short, left = "-" + left[0], left[1:]
        transformations: dict[str | None, Callable[[str], str]] = {None: lambda x: x}
        if more_magic:
            transformations["lowercase"] = lambda x: x.lower()
            transformations["uppercase"] = lambda x: x.upper()
        # try identity, lowercase, uppercase, iff such resolves uniquely
        # (ie if upper and lowercase are not both defined)
        similar: list[_Option] = []
        de_abbreviated = False
        for transform_name, transform in transformations.items():
            transformed = list(set([transform(o.short) for o in options if o.short]))
            no_collisions = len(
                [o for o in options if o.short and transformed.count(transform(o.short)) == 1]
            )  # == len(transformed)
            if no_collisions:
                similar = [o for o in options if o.short and transform(o.short) == transform(short)]
                if similar:
                    if transform_name:
                        print(
                            f"NB: Corrected {short} to {similar[0].short} " f"via {transform_name}"
                        )
                    break
            # if transformations do not resolve, try abbreviations of 'longer' forms
            # iff such resolves uniquely (ie if no two longer forms begin with the
            # same letter)
            if not similar and more_magic:
                abbreviated = [
                    transform(o.longer[1:3]) for o in options if o.longer and not o.short
                ] + [transform(o.short) for o in options if o.short and not o.longer]
                nonredundantly_abbreviated_options = [
                    o for o in options if o.longer and abbreviated.count(short) == 1
                ]
                no_collisions = len(nonredundantly_abbreviated_options) == len(abbreviated)
                if no_collisions:
                    for o in options:
                        if (
                            not o.short
                            and o.longer
                            and transform(short) == transform(o.longer[1:3])
                        ):
                            similar = [o]
                            print(
                                f"NB: Corrected {short} to {similar[0].longer} "
                                f"via abbreviation (case change: {transform_name})"
                            )
                            break
                if len(similar):
                    de_abbreviated = True
                    break
        if len(similar) > 1:
            raise DocoptLanguageError(f"{short} is specified ambiguously {len(similar)} times")
        elif len(similar) < 1:
            o = _Option(short, None, 0)
            options.append(o)
            if tokens.error is DocoptExit:
                o = _Option(short, None, 0, True)
        else:
            if de_abbreviated:
                option_short_value = None
            else:
                option_short_value = transform(short)
            o = _Option(
                option_short_value,
                similar[0].longer,
                similar[0].argcount,
                similar[0].value,
            )
            value = None
            current_token = tokens.current()
            if o.argcount != 0:
                if left == "":
                    if current_token is None or current_token == "--":
                        raise tokens.error("%s requires argument" % short)
                    else:
                        value = tokens.move()
                else:
                    value = left
                    left = ""
            if tokens.error is DocoptExit:
                o.value = value if value is not None else True
        parsed.append(o)
    return parsed


def _parse_pattern(source: str, options: list[_Option]) -> _Required:
    tokens = _Tokens.from_pattern(source)
    result = _parse_expr(tokens, options)
    if tokens.current() is not None:
        raise tokens.error("unexpected ending: %r" % " ".join(tokens))
    return _Required(*result)


def _parse_expr(tokens: _Tokens, options: list[_Option]) -> list[_Pattern]:
    """expr ::= seq ( '|' seq )* ;"""
    result: list[_Pattern] = []
    seq_0: list[_Pattern] = _parse_seq(tokens, options)
    if tokens.current() != "|":
        return seq_0
    if len(seq_0) > 1:
        result.append(_Required(*seq_0))
    else:
        result += seq_0
    while tokens.current() == "|":
        tokens.move()
        seq_1 = _parse_seq(tokens, options)
        if len(seq_1) > 1:
            result += [_Required(*seq_1)]
        else:
            result += seq_1
    return [_Either(*result)]


def _parse_seq(tokens: _Tokens, options: list[_Option]) -> list[_Pattern]:
    """seq ::= ( atom [ '...' ] )* ;"""
    result: list[_Pattern] = []
    while tokens.current() not in [None, "]", ")", "|"]:
        atom = _parse_atom(tokens, options)
        if tokens.current() == "...":
            atom = [_OneOrMore(*atom)]
            tokens.move()
        result += atom
    return result


def _parse_atom(tokens: _Tokens, options: list[_Option]) -> list[_Pattern]:
    """atom ::= '(' expr ')' | '[' expr ']' | 'options'
    | longer | shorts | argument | command ;
    """
    token = tokens.current()
    if not token:
        return [_Command(tokens.move())]  # pragma: no cover
    elif token in "([":
        tokens.move()
        matching = {"(": ")", "[": "]"}[token]
        pattern = {"(": _Required, "[": _NotRequired}[token]
        matched_pattern = pattern(*_parse_expr(tokens, options))
        if tokens.move() != matching:
            raise tokens.error("unmatched '%s'" % token)
        return [matched_pattern]
    elif token == "options":
        tokens.move()
        return [_OptionsShortcut()]
    elif token.startswith("--") and token != "--":
        return _parse_longer(tokens, options)
    elif token.startswith("-") and token not in ("-", "--"):
        return _parse_shorts(tokens, options)
    elif token.startswith("<") and token.endswith(">") or token.isupper():
        return [_Argument(tokens.move())]
    else:
        return [_Command(tokens.move())]


def _parse_argv(
    tokens: _Tokens,
    options: list[_Option],
    options_first: bool = False,
    more_magic: bool = False,
) -> list[_Pattern]:
    """Parse command-line argument vector.

    If options_first:
        argv ::= [ longer | shorts ]* [ argument ]* [ '--' [ argument ]* ] ;
    else:
        argv ::= [ longer | shorts | argument ]* [ '--' [ argument ]* ] ;

    """

    def isanumber(x):
        try:
            float(x)
            return True
        except ValueError:
            return False

    parsed: list[_Pattern] = []
    current_token = tokens.current()
    while current_token is not None:
        if current_token == "--":
            return parsed + [_Argument(None, v) for v in tokens]
        elif current_token.startswith("--"):
            parsed += _parse_longer(tokens, options, argv=True, more_magic=more_magic)
        elif (
            current_token.startswith("-") and current_token != "-" and not isanumber(current_token)
        ):
            parsed += _parse_shorts(tokens, options, more_magic=more_magic)
        elif options_first:
            return parsed + [_Argument(None, v) for v in tokens]
        else:
            parsed.append(_Argument(None, tokens.move()))
        current_token = tokens.current()
    return parsed


class _DocSections(NamedTuple):
    before_usage: str
    usage_header: str
    usage_body: str
    after_usage: str


def _parse_docstring_sections(docstring: str) -> _DocSections:
    """Partition the docstring into the main sections.

    The docstring is returned, split into a tuple of 4 pieces: text before the
    usage section, the usage section header, the usage section body and text
    following the usage section.
    """
    usage_pattern = r"""
    # Any number of lines (that don't include usage:) precede the usage section
    \A(?P<before_usage>(?:(?!.*\busage:).*\n)*)
    # The `usage:` section header.
    ^(?P<usage_header>.*\busage:)
    (?P<usage_body>
        # The first line of the body may follow the header without a line break:
        (?:.*(?:\n|\Z))
        # Any number of additional indented lines
        (?:[ \t].*(?:\n|\Z))*
    )
    # Everything else
    (?P<after_usage>(?:.|\n)*)\Z
    """
    match = re.match(usage_pattern, docstring, flags=re.M | re.I | re.VERBOSE)
    if not match:
        raise DocoptLanguageError(
            'Failed to parse doc: "usage:" section (case-insensitive) not found. '
            "Check http://docopt.org/ for examples of how your doc should look."
        )
    before, header, body, after = match.groups()
    return _DocSections(before, header, body, after)


def _parse_options(docstring: str) -> list[_Option]:
    """Parse the option descriptions from the help text.

    `docstring` is the sub-section of the overall docstring that option
    descriptions should be parsed from. It must not contain the "usage:"
    section, as wrapped lines in the usage pattern can be misinterpreted as
    option descriptions.

    Option descriptions appear below the usage patterns, They define synonymous
    long and short options, options that have arguments, and the default values
    of options' arguments. They look like this:

    ```
        -v, --verbose             Be more verbose
        -n COUNT, --number COUNT  The number of times to
                                do the thing  [default: 42]
    ```
    """
    option_start = r"""
    # Option descriptions begin on a new line
    ^
    # They may occur on the same line as an options: section heading
    (?:.*options:)?
    # They can be indented with whitespace
    [ \t]*
    # The description itself starts with the short or long flag (-x or --xxx)
    (-\S)
    """
    parts = re.split(option_start, docstring, flags=re.M | re.I | re.VERBOSE)[1:]
    return [_Option.parse(start + rest) for (start, rest) in zip(parts[0::2], parts[1::2])]


def _lint_docstring(sections: _DocSections):
    """Report apparent mistakes in the docstring format."""
    if re.search("options:", sections.usage_body, flags=re.I):
        raise DocoptLanguageError(
            'Failed to parse docstring: "options:" (case-insensitive) was '
            'found in "usage:" section. Use a blank line after the usage, or '
            "start the next section without leading whitespace."
        )
    if re.search("usage:", sections.usage_body + sections.after_usage, flags=re.I):
        raise DocoptLanguageError(
            'Failed to parse docstring: More than one "usage:" ' "(case-insensitive) section found."
        )
    if sections.usage_body.strip() == "":
        raise DocoptLanguageError(
            'Failed to parse docstring: "usage:" section is empty.'
            "Check http://docopt.org/ for examples of how your doc should look."
        )


def _formal_usage(usage: str) -> str:
    program_name, *tokens = usage.split()
    return "( " + " ".join(") | (" if s == program_name else s for s in tokens) + " )"


def _extras(default_help: bool, version: None, options: list[_Pattern], docstring: str) -> None:
    if default_help and any(
        (o.name in ("-h", "--help")) and o.value for o in options if isinstance(o, _Option)
    ):
        print(docstring.strip("\n"))
        sys.exit()
    if version and any(
        o.name == "--version" and o.value for o in options if isinstance(o, _Option)
    ):
        print(version)
        sys.exit()


class ParsedOptions(dict):
    def __repr__(self):
        return "{%s}" % ",\n ".join("%r: %r" % i for i in sorted(self.items()))

    def __getattr__(self, name: str) -> str | bool | None:
        return self.get(name) or {
            name: self.get(k)
            for k in self.keys()
            if name in [k.lstrip("-").replace("-", "_"), k.lstrip("<").rstrip(">")]
        }.get(name)


def docopt(
    docstring: str,
    argv: list[str] | str | None = None,
    default_help: bool = True,
    version: Any = None,
    options_first: bool = False,
) -> ParsedOptions:
    """Parse `argv` based on command-line interface described in `docstring`.

    `docopt` creates your command-line interface based on its
    description that you pass as `docstring`. Such description can contain
    --options, <positional-argument>, commands, which could be
    [optional], (required), (mutually | exclusive) or repeated...

    Parameters
    ----------
    docstring : str
        Description of your command-line interface.
    argv : list of str or str, optional
        Argument vector to be parsed. sys.argv[1:] is used if not
        provided. If str is passed, the string is split on whitespace.
    default_help : bool (default: True)
        Set to False to disable automatic help on -h or --help
        options.
    version : any object
        If passed, the object will be printed if --version is in
        `argv`.
    options_first : bool (default: False)
        Set to True to require options precede positional arguments,
        i.e. to forbid options and positional arguments intermix.

    Returns
    -------
    arguments: dict-like
        A dictionary, where keys are names of command-line elements
        such as e.g. "--verbose" and "<path>", and values are the
        parsed values of those elements. Also supports dot access.

    Example
    -------
    >>> from docopt import docopt
    >>> doc = '''
    ... Usage:
    ...     my_program tcp <host> <port> [--timeout=<seconds>]
    ...     my_program serial <port> [--baud=<n>] [--timeout=<seconds>]
    ...     my_program (-h | --help | --version)
    ...
    ... Options:
    ...     -h, --help  Show this screen and exit.
    ...     --baud=<n>  Baudrate [default: 9600]
    ... '''
    >>> argv = ['tcp', '127.0.0.1', '80', '--timeout', '30']
    >>> docopt(doc, argv)
    {'--baud': '9600',
     '--help': False,
     '--timeout': '30',
     '--version': False,
     '<host>': '127.0.0.1',
     '<port>': '80',
     'serial': False,
     'tcp': True}
    """
    argv = sys.argv[1:] if argv is None else argv
    sections = _parse_docstring_sections(docstring)
    _lint_docstring(sections)
    DocoptExit.usage = sections.usage_header + sections.usage_body
    options = [
        *_parse_options(sections.before_usage),
        *_parse_options(sections.after_usage),
    ]
    pattern = _parse_pattern(_formal_usage(sections.usage_body), options)
    pattern_options = set(pattern.flat(_Option))
    for options_shortcut in pattern.flat(_OptionsShortcut):
        options_shortcut.children = [opt for opt in options if opt not in pattern_options]
    parsed_arg_vector = _parse_argv(_Tokens(argv), list(options), options_first)
    _extras(default_help, version, parsed_arg_vector, docstring)
    matched, left, collected = pattern.fix().match(parsed_arg_vector)
    if matched and left == []:
        return ParsedOptions((a.name, a.value) for a in (pattern.flat() + collected))
    if left:
        raise DocoptExit(f"Warning: found unmatched (duplicate?) arguments {left}")
    raise DocoptExit(collected=collected, left=left)
