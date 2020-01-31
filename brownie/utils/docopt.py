"""Docopt is a Pythonic command-line interface parser that will make you smile.

Now: with levenshtein based spellcheck, flag extension (de-abbreviation), and capitalization fixes.
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

This file has been modified to meet Brownie's linting requirements,
the original version is available at:

github.com/bazaar-projects/docopt-ng/blob/bbed40a2335686d2e14ac0e6c3188374dc4784da/docopt.py
"""

import inspect
import re
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

__all__ = ["docopt", "magic_docopt", "magic"]
__version__ = "0.7.2"


def levenshtein_norm(source: str, target: str) -> float:
    """Calculates the normalized Levenshtein distance between two string
    arguments. The result will be a float in the range [0.0, 1.0], with 1.0
    signifying the biggest possible distance between strings with these lengths
    """

    # Compute Levenshtein distance using helper function. The max is always
    # just the length of the longer string, so this is used to normalize result
    # before returning it
    distance = levenshtein(source, target)
    return float(distance) / max(len(source), len(target))


def levenshtein(source: str, target: str) -> int:
    """Computes the Levenshtein
    (https://en.wikipedia.org/wiki/Levenshtein_distance)
    and restricted Damerau-Levenshtein
    (https://en.wikipedia.org/wiki/Damerau%E2%80%93Levenshtein_distance)
    distances between two Unicode strings with given lengths using the
    Wagner-Fischer algorithm
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

    # Iterate through rest of matrix, filling it in with Levenshtein
    # distances for the remaining prefix combinations
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
        self, message: str = "", collected: List["Pattern"] = None, left: List["Pattern"] = None
    ) -> None:
        self.collected = collected if collected is not None else []
        self.left = left if left is not None else []
        SystemExit.__init__(self, (message + "\n" + self.usage).strip())


class Pattern:
    def __init__(
        self, name: Optional[str], value: Optional[Union[List[str], str, int]] = None
    ) -> None:
        self._name, self.value = name, value

    @property
    def name(self) -> Optional[str]:
        return self._name

    def __eq__(self, other: Any) -> bool:
        return repr(self) == repr(other)

    def __hash__(self) -> int:
        return hash(repr(self))


def transform(pattern: "BranchPattern") -> "Either":
    """Expand pattern into an (almost) equivalent one, but with single Either.

    Example: ((-a | -b) (-c | -d)) => (-a -c | -a -d | -b -c | -b -d)
    Quirks: [-a] => (-a), (-a...) => (-a -a)

    """
    result = []
    groups = [[pattern]]
    while groups:
        children = groups.pop(0)
        parents = [Required, NotRequired, OptionsShortcut, Either, OneOrMore]
        if any(t in map(type, children) for t in parents):
            child = [c for c in children if type(c) in parents][0]
            children.remove(child)
            if type(child) is Either:
                for c in child.children:
                    groups.append([c] + children)
            elif type(child) is OneOrMore:
                groups.append(child.children * 2 + children)
            else:
                groups.append(child.children + children)
        else:
            result.append(children)
    return Either(*[Required(*e) for e in result])


TSingleMatch = Tuple[Union[int, None], Union["LeafPattern", None]]


class LeafPattern(Pattern):

    """Leaf/terminal node of a pattern tree."""

    def __repr__(self) -> str:
        return "%s(%r, %r)" % (self.__class__.__name__, self.name, self.value)

    def single_match(self, left: List["LeafPattern"]) -> TSingleMatch:
        raise NotImplementedError  # pragma: no cover

    def flat(self, *types) -> List["LeafPattern"]:
        return [self] if not types or type(self) in types else []

    def match(
        self, left: List["LeafPattern"], collected: List["Pattern"] = None
    ) -> Tuple[bool, List["LeafPattern"], List["Pattern"]]:
        collected = [] if collected is None else collected
        increment: Optional[Any] = None
        pos, match = self.single_match(left)
        if match is None or pos is None:
            return False, left, collected
        left_ = left[:pos] + left[(pos + 1) :]
        same_name = [a for a in collected if a.name == self.name]
        if type(self.value) == int and len(same_name) > 0:
            if isinstance(same_name[0].value, int):
                same_name[0].value += 1
            return True, left_, collected
        if type(self.value) == int and not same_name:
            match.value = 1
            return True, left_, collected + [match]
        if same_name and type(self.value) == list:
            if type(match.value) == str:
                increment = [match.value]
            if same_name[0].value is not None and increment is not None:
                if isinstance(same_name[0].value, type(increment)):
                    same_name[0].value += increment
            return True, left_, collected
        elif not same_name and type(self.value) == list:
            if isinstance(match.value, str):
                match.value = [match.value]
            return True, left_, collected + [match]
        return True, left_, collected + [match]


class BranchPattern(Pattern):

    """Branch/inner node of a pattern tree."""

    def __init__(self, *children) -> None:
        self.children = list(children)

    def match(self, left: List["Pattern"], collected: List["Pattern"] = None) -> Any:
        raise NotImplementedError  # pragma: no cover

    def fix(self) -> "BranchPattern":
        self.fix_identities()
        self.fix_repeating_arguments()
        return self

    def fix_identities(self, uniq: Optional[Any] = None) -> None:
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

    def fix_repeating_arguments(self) -> "BranchPattern":
        """Fix elements that should accumulate/increment values."""
        either = [list(child.children) for child in transform(self).children]
        for case in either:
            for e in [child for child in case if case.count(child) > 1]:
                if type(e) is Argument or type(e) is Option and e.argcount:
                    if e.value is None:
                        e.value = []
                    elif type(e.value) is not list:
                        e.value = e.value.split()
                if type(e) is Command or type(e) is Option and e.argcount == 0:
                    e.value = 0
        return self

    def __repr__(self) -> str:
        return "%s(%s)" % (self.__class__.__name__, ", ".join(repr(a) for a in self.children))

    def flat(self, *types) -> Any:
        if type(self) in types:
            return [self]
        return sum([child.flat(*types) for child in self.children], [])


class Argument(LeafPattern):
    def single_match(self, left: List[LeafPattern]) -> TSingleMatch:
        for n, pattern in enumerate(left):
            if type(pattern) is Argument:
                return n, Argument(self.name, pattern.value)
        return None, None


class Command(Argument):
    def __init__(self, name: Union[str, None], value: bool = False) -> None:
        self._name, self.value = name, value

    def single_match(self, left: List[LeafPattern]) -> TSingleMatch:
        for n, pattern in enumerate(left):
            if type(pattern) is Argument:
                if pattern.value == self.name:
                    return n, Command(self.name, True)
                else:
                    break
        return None, None


class Option(LeafPattern):
    def __init__(
        self,
        short: Optional[str] = None,
        longer: Optional[str] = None,
        argcount: int = 0,
        value: Union[List[str], str, int, None] = False,
    ) -> None:
        assert argcount in (0, 1)
        self.short, self.longer, self.argcount = short, longer, argcount
        self.value = None if value is False and argcount else value

    @classmethod
    def parse(class_, option_description: str) -> "Option":
        short, longer, argcount, value = None, None, 0, False
        options, _, description = option_description.strip().partition("  ")
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
        return class_(short, longer, argcount, value)

    def single_match(self, left: List[LeafPattern]) -> TSingleMatch:
        for n, pattern in enumerate(left):
            if self.name == pattern.name:
                return n, pattern
        return None, None

    @property
    def name(self) -> Optional[str]:
        return self.longer or self.short

    def __repr__(self) -> str:
        return "Option(%r, %r, %r, %r)" % (self.short, self.longer, self.argcount, self.value)


class Required(BranchPattern):
    def match(self, left: List["Pattern"], collected: List["Pattern"] = None) -> Any:
        collected = [] if collected is None else collected
        original_collected = collected
        original_left = left
        for pattern in self.children:
            matched, left, collected = pattern.match(left, collected)
            if not matched:
                return False, original_left, original_collected
        return True, left, collected


class NotRequired(BranchPattern):
    def match(self, left: List["Pattern"], collected: List["Pattern"] = None) -> Any:
        collected = [] if collected is None else collected
        for pattern in self.children:
            _, left, collected = pattern.match(left, collected)
        return True, left, collected


class OptionsShortcut(NotRequired):

    """Marker/placeholder for [options] shortcut."""


class OneOrMore(BranchPattern):
    def match(self, left: List[Pattern], collected: List[Pattern] = None) -> Any:
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


class Either(BranchPattern):
    def match(self, left: List["Pattern"], collected: List["Pattern"] = None) -> Any:
        collected = [] if collected is None else collected
        outcomes = []
        for pattern in self.children:
            matched, _, _ = outcome = pattern.match(left, collected)
            if matched:
                outcomes.append(outcome)
        if outcomes:
            return min(outcomes, key=lambda outcome: len(outcome[1]))
        return False, left, collected


class Tokens(list):
    def __init__(
        self,
        source: Union[List[str], str],
        error: Union[Type[DocoptExit], Type[DocoptLanguageError]] = DocoptExit,
    ) -> None:
        if isinstance(source, list):
            self += source
        else:
            self += source.split()
        self.error = error

    @staticmethod
    def from_pattern(source: str) -> "Tokens":
        source = re.sub(r"([\[\]\(\)\|]|\.\.\.)", r" \1 ", source)
        fragments = [s for s in re.split(r"\s+|(\S*<.*?>)", source) if s]
        return Tokens(fragments, error=DocoptLanguageError)

    def move(self) -> Optional[str]:
        return self.pop(0) if len(self) else None

    def current(self) -> Optional[str]:
        return self[0] if len(self) else None


def parse_longer(
    tokens: Tokens, options: List[Option], argv: bool = False, more_magic: bool = False
) -> List[Pattern]:
    """longer ::= '--' chars [ ( ' ' | '=' ) chars ] ;"""
    current_token = tokens.move()
    if current_token is None or not current_token.startswith("--"):
        raise tokens.error(
            f"parse_longer got what appears to be an invalid token: {current_token}"
        )  # pragma: no cover
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
        raise tokens.error(f"{longer} is not a unique prefix: {similar}?")  # pragma: no cover
    elif len(similar) < 1:
        argcount = 1 if maybe_eq == "=" else 0
        o = Option(None, longer, argcount)
        options.append(o)
        if tokens.error is DocoptExit:
            o = Option(None, longer, argcount, value if argcount else True)
    else:
        o = Option(similar[0].short, similar[0].longer, similar[0].argcount, similar[0].value)
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


def parse_shorts(tokens: Tokens, options: List[Option], more_magic: bool = False) -> List[Pattern]:
    """shorts ::= '-' ( chars )* [ [ ' ' ] chars ] ;"""
    token = tokens.move()
    if token is None or not token.startswith("-") or token.startswith("--"):
        raise ValueError(
            f"parse_shorts got what appears to be an invalid token: {token}"
        )  # pragma: no cover
    left = token.lstrip("-")
    parsed: List[Pattern] = []
    while left != "":
        short, left = "-" + left[0], left[1:]
        transformations: Dict[Union[None, str], Callable[[str], str]] = {None: lambda x: x}
        if more_magic:
            transformations["lowercase"] = lambda x: x.lower()
            transformations["uppercase"] = lambda x: x.upper()
        # try identity, lowercase, uppercase,
        # iff such resolves uniquely (ie if upper and lowercase are not both defined)
        similar: List[Option] = []
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
                        print(f"NB: Corrected {short} to {similar[0].short} via {transform_name}")
                    break
            # if transformations do not resolve, try abbreviations of 'longer' forms
            # iff such resolves uniquely (ie if no two longer forms begin with the same letter)
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
                                f"NB: Corrected {short} to {similar[0].longer} via abbreviation"
                                " (case change: {transform_name})"
                            )
                            break
                if len(similar):
                    de_abbreviated = True
                    break
        if len(similar) > 1:
            raise tokens.error("%s is specified ambiguously %d times" % (short, len(similar)))
        elif len(similar) < 1:
            o = Option(short, None, 0)
            options.append(o)
            if tokens.error is DocoptExit:
                o = Option(short, None, 0, True)
        else:
            if de_abbreviated:
                option_short_value = None
            else:
                option_short_value = transform(short)
            o = Option(option_short_value, similar[0].longer, similar[0].argcount, similar[0].value)
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


def parse_pattern(source: str, options: List[Option]) -> Required:
    tokens = Tokens.from_pattern(source)
    result = parse_expr(tokens, options)
    if tokens.current() is not None:
        raise tokens.error("unexpected ending: %r" % " ".join(tokens))
    return Required(*result)


def parse_expr(tokens: Tokens, options: List[Option]) -> List[Pattern]:
    """expr ::= seq ( '|' seq )* ;"""
    result: List[Pattern] = []
    seq_0: List[Pattern] = parse_seq(tokens, options)
    if tokens.current() != "|":
        return seq_0
    if len(seq_0) > 1:
        result.append(Required(*seq_0))
    else:
        result += seq_0
    while tokens.current() == "|":
        tokens.move()
        seq_1 = parse_seq(tokens, options)
        if len(seq_1) > 1:
            result += [Required(*seq_1)]
        else:
            result += seq_1
    return [Either(*result)]


def parse_seq(tokens: Tokens, options: List[Option]) -> List[Pattern]:
    """seq ::= ( atom [ '...' ] )* ;"""
    result: List[Pattern] = []
    while tokens.current() not in [None, "]", ")", "|"]:
        atom = parse_atom(tokens, options)
        if tokens.current() == "...":
            atom = [OneOrMore(*atom)]
            tokens.move()
        result += atom
    return result


def parse_atom(tokens: Tokens, options: List[Option]) -> List[Pattern]:
    """atom ::= '(' expr ')' | '[' expr ']' | 'options'
             | longer | shorts | argument | command ;
    """
    token = tokens.current()
    if not token:
        return [Command(tokens.move())]  # pragma: no cover
    elif token in "([":
        tokens.move()
        matching = {"(": ")", "[": "]"}[token]
        pattern = {"(": Required, "[": NotRequired}[token]
        matched_pattern = pattern(*parse_expr(tokens, options))
        if tokens.move() != matching:
            raise tokens.error("unmatched '%s'" % token)
        return [matched_pattern]
    elif token == "options":
        tokens.move()
        return [OptionsShortcut()]
    elif token.startswith("--") and token != "--":
        return parse_longer(tokens, options)
    elif token.startswith("-") and token not in ("-", "--"):
        return parse_shorts(tokens, options)
    elif token.startswith("<") and token.endswith(">") or token.isupper():
        return [Argument(tokens.move())]
    else:
        return [Command(tokens.move())]


def parse_argv(
    tokens: Tokens, options: List[Option], options_first: bool = False, more_magic: bool = False
) -> List[Pattern]:
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

    parsed: List[Pattern] = []
    current_token = tokens.current()
    while current_token is not None:
        if current_token == "--":
            return parsed + [Argument(None, v) for v in tokens]
        elif current_token.startswith("--"):
            parsed += parse_longer(tokens, options, argv=True, more_magic=more_magic)
        elif (
            current_token.startswith("-") and current_token != "-" and not isanumber(current_token)
        ):
            parsed += parse_shorts(tokens, options, more_magic=more_magic)
        elif options_first:
            return parsed + [Argument(None, v) for v in tokens]
        else:
            parsed.append(Argument(None, tokens.move()))
        current_token = tokens.current()
    return parsed


def parse_defaults(docstring: str) -> List[Option]:
    defaults = []
    for s in parse_section("options:", docstring):
        options_literal, _, s = s.partition(":")
        if " " in options_literal:
            _, _, options_literal = options_literal.partition(" ")
        assert options_literal.lower().strip() == "options"
        split = re.split(r"\n[ \t]*(-\S+?)", "\n" + s)[1:]
        split = [s1 + s2 for s1, s2 in zip(split[::2], split[1::2])]
        for s in split:
            if s.startswith("-"):
                arg, _, description = s.partition("  ")
                flag, _, var = arg.replace("=", " ").partition(" ")
                option = Option.parse(s)
                defaults.append(option)
    return defaults


def parse_section(name: str, source: str) -> List[str]:
    pattern = re.compile(
        "^([^\n]*" + name + "[^\n]*\n?(?:[ \t].*?(?:\n|$))*)", re.IGNORECASE | re.MULTILINE
    )
    r = [s.strip() for s in pattern.findall(source) if s.strip().lower() != name.lower()]
    return r


def formal_usage(section: str) -> str:
    _, _, section = section.partition(":")  # drop "usage:"
    pu = section.split()
    return "( " + " ".join(") | (" if s == pu[0] else s for s in pu[1:]) + " )"


def extras(default_help: bool, version: None, options: List[Pattern], docstring: str) -> None:
    if default_help and any(
        (o.name in ("-h", "--help")) and o.value for o in options if isinstance(o, Option)
    ):
        print(docstring.strip("\n"))
        sys.exit()
    if version and any(o.name == "--version" and o.value for o in options if isinstance(o, Option)):
        print(version)
        sys.exit()


class ParsedOptions(dict):
    def __repr__(self):
        return "{%s}" % ",\n ".join("%r: %r" % i for i in sorted(self.items()))

    def __getattr__(self, name: str) -> Optional[Union[str, bool]]:
        return self.get(name) or {
            name: self.get(k)
            for k in self.keys()
            if name in [k.lstrip("-"), k.lstrip("<").rstrip(">")]
        }.get(name)


def docopt(
    docstring: Optional[str] = None,
    argv: Optional[Union[List[str], str]] = None,
    default_help: bool = True,
    version: Any = None,
    options_first: bool = False,
    more_magic: bool = False,
) -> ParsedOptions:
    """Parse `argv` based on command-line interface described in `doc`.

    `docopt` creates your command-line interface based on its
    description that you pass as `docstring`. Such description can contain
    --options, <positional-argument>, commands, which could be
    [optional], (required), (mutually | exclusive) or repeated...

    Parameters
    ----------
    docstring : str (default: first __doc__ in parent scope)
        Description of your command-line interface.
    argv : list of str, optional
        Argument vector to be parsed. sys.argv[1:] is used if not
        provided.
    default_help : bool (default: True)
        Set to False to disable automatic help on -h or --help
        options.
    version : any object
        If passed, the object will be printed if --version is in
        `argv`.
    options_first : bool (default: False)
        Set to True to require options precede positional arguments,
        i.e. to forbid options and positional arguments intermix.
    more_magic : bool (default: False)
        Try to be extra-helpful; pull results into globals() of caller as 'arguments',
        offer advanced pattern-matching and spellcheck.
        Also activates if `docopt` aliased to a name containing 'magic'.

    Returns
    -------
    arguments: dict-like
        A dictionary, where keys are names of command-line elements
        such as e.g. "--verbose" and "<path>", and values are the
        parsed values of those elements. Also supports dot acccess.

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
    maybe_frame = inspect.currentframe()
    if maybe_frame:
        parent_frame = doc_parent_frame = magic_parent_frame = maybe_frame.f_back
    if not more_magic:  # make sure 'magic' isn't in the calling name
        while not more_magic and magic_parent_frame:
            imported_as = {
                v: k
                for k, v in magic_parent_frame.f_globals.items()
                if hasattr(v, "__name__") and v.__name__ == docopt.__name__
            }.get(docopt)
            if imported_as and "magic" in imported_as:
                more_magic = True
            else:
                magic_parent_frame = magic_parent_frame.f_back
    if not docstring:  # go look for one, if none exists, raise Exception
        while not docstring and doc_parent_frame:
            docstring = doc_parent_frame.f_locals.get("__doc__")
            if not docstring:
                doc_parent_frame = doc_parent_frame.f_back
        if not docstring:
            raise DocoptLanguageError(
                "Either __doc__ must be defined in the scope of a parent "
                "or passed as the first argument."
            )
    output_value_assigned = False
    if more_magic and parent_frame:
        import dis

        instrs = dis.get_instructions(parent_frame.f_code)
        for instr in instrs:
            if instr.offset == parent_frame.f_lasti:
                break
        assert instr.opname.startswith("CALL_")
        MAYBE_STORE = next(instrs)
        if MAYBE_STORE and (
            MAYBE_STORE.opname.startswith("STORE") or MAYBE_STORE.opname.startswith("RETURN")
        ):
            output_value_assigned = True
    usage_sections = parse_section("usage:", docstring)
    if len(usage_sections) == 0:
        raise DocoptLanguageError(
            '"usage:" section (case-insensitive) not found. Perhaps missing indentation?'
        )
    if len(usage_sections) > 1:
        raise DocoptLanguageError('More than one "usage:" (case-insensitive).')
    options_pattern = re.compile(r"\n\s*?options:", re.IGNORECASE)
    if options_pattern.search(usage_sections[0]):
        raise DocoptExit(
            "Warning: options (case-insensitive) was found in usage."
            "Use a blank line between each section.."
        )
    DocoptExit.usage = usage_sections[0]
    options = parse_defaults(docstring)
    pattern = parse_pattern(formal_usage(DocoptExit.usage), options)
    pattern_options = set(pattern.flat(Option))
    for options_shortcut in pattern.flat(OptionsShortcut):
        doc_options = parse_defaults(docstring)
        options_shortcut.children = [opt for opt in doc_options if opt not in pattern_options]
    parsed_arg_vector = parse_argv(Tokens(argv), list(options), options_first, more_magic)
    extras(default_help, version, parsed_arg_vector, docstring)
    matched, left, collected = pattern.fix().match(parsed_arg_vector)
    if matched and left == []:
        output_obj = ParsedOptions((a.name, a.value) for a in (pattern.flat() + collected))
        target_parent_frame = parent_frame or magic_parent_frame or doc_parent_frame
        if more_magic and target_parent_frame and not output_value_assigned:
            if not target_parent_frame.f_globals.get("arguments"):
                target_parent_frame.f_globals["arguments"] = output_obj
        return output_obj
    raise DocoptExit(collected=collected, left=left)


magic = magic_docopt = docopt
