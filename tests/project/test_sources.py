#!/usr/bin/python3

import pytest
from packaging.version import Version

from brownie import compile_source
from brownie.exceptions import NamespaceCollision, PragmaError
from brownie.project import sources

MESSY_SOURCE = """
  pragma  solidity>=0.4.22   <0.7.0  ;contract Foo{} interface Bar
    {} enum Struct { Contract }
abstract contract Baz is Foo {} struct  Interface  { uint256 Abstract;
}    library   Potato{} pragma     solidity    ^0.6.0;  contract Foo2 is
Foo{ enum E {a, b}  struct S {bool b;
}}  library Bar2{}"""


@pytest.fixture(scope="module")
def sourceobj(solc5source):
    yield sources.Sources(
        {"path/to/Foo.sol": solc5source}, {"interfaces/Baz.vy": "@external\ndef bar(): pass"}
    )


def test_namespace_collisions(solc5source):
    # contract collision
    with pytest.raises(NamespaceCollision):
        sources.Sources({"foo.sol": solc5source, "bar.sol": solc5source}, {})
    # interface collision
    with pytest.raises(NamespaceCollision):
        sources.Sources({}, {"foo.sol": solc5source, "bar.sol": solc5source})
    # solc / vyper collision
    with pytest.raises(NamespaceCollision):
        sources.Sources({"foo.sol": solc5source, "Foo.vy": "@external\ndef bar(): pass"}, {})


def test_contract_interface_collisions(solc5source):
    # contract / interface collision
    sources.Sources({"foo.sol": solc5source}, {"bar.sol": solc5source})
    sources.Sources({"foo.sol": solc5source}, {"Foo.vy": "@external\ndef bar(): pass"})


def test_get_path_list(sourceobj):
    assert sourceobj.get_path_list() == ["path/to/Foo.sol"]


def test_get_contract_list(sourceobj):
    assert sourceobj.get_contract_list() == ["Bar", "Foo"]


def test_get_interface_list(sourceobj):
    assert sourceobj.get_interface_list() == ["Baz"]


def test_get_source_path(sourceobj):
    assert sourceobj.get_source_path("Bar") == "path/to/Foo.sol"
    assert sourceobj.get_source_path("Baz") == "interfaces/Baz.vy"
    with pytest.raises(KeyError):
        sourceobj.get_source_path("fooboo")


def test_get_contract_names():
    names = sources.get_contract_names(MESSY_SOURCE)
    assert names == [
        ("Foo", "contract"),
        ("Bar", "interface"),
        ("Baz", "abstract contract"),
        ("Potato", "library"),
        ("Foo2", "contract"),
        ("Bar2", "library"),
    ]


def test_load_messy_project():
    project = compile_source(MESSY_SOURCE)
    assert list(project.keys()) == ["Bar2", "Foo", "Foo2", "Potato"]


def test_get_pragma_spec():
    spec = sources.get_pragma_spec(MESSY_SOURCE)

    assert str(spec) == ">=0.4.22 <0.7.0 && ^0.6.0"
    assert Version("0.6.12") in spec
    assert Version("0.5.17") not in spec


def test_get_pragma_spec_ignores_comments_and_strings():
    source = """
    // pragma solidity 0.4.22;
    contract Foo {
        string constant BAR = "pragma solidity 0.5.0;";
    }
    pragma solidity ^0.6.0;
    """

    assert sources.get_pragma_spec(source).select(
        [Version("0.5.17"), Version("0.6.12")]
    ) == Version("0.6.12")


def test_get_pragma_spec_rejects_solc_prerelease_match_expressions():
    with pytest.raises(PragmaError):
        sources.get_pragma_spec("pragma solidity >=0.8.20-rc.1;")


def test_get_pragma_spec_solc_tilde_range():
    spec = sources.get_pragma_spec("pragma solidity ~0.8.20;")

    assert Version("0.8.20") in spec
    assert Version("0.8.28") in spec
    assert Version("0.9.0") not in spec


def test_get_pragma_spec_solc_caret_zero_major_matches_solc():
    spec = sources.get_pragma_spec("pragma solidity ^0.0.3;")

    assert Version("0.0.3") in spec
    assert Version("0.0.4") in spec
    assert Version("0.1.0") not in spec


@pytest.mark.parametrize(
    "version, matching_version",
    [
        ("0.1.0b16", Version("0.1.0b16")),
        ("0.1.0Beta17", Version("0.1.0b17")),
        (">=0.1.0-beta.16", Version("0.1.0b16")),
        ("^0.2.0", Version("0.2.16")),
        ("<=0.2.4", Version("0.2.4")),
    ],
)
def test_get_vyper_pragma_spec_legacy_version(version, matching_version):
    source = f"""# @version {version}"""
    spec = sources.get_vyper_pragma_spec(source)

    assert matching_version in spec


def test_get_vyper_pragma_spec_legacy_uses_npm_caret():
    spec = sources.get_vyper_pragma_spec("# @version ^0.0.3")

    assert Version("0.0.3") in spec
    assert Version("0.0.4") not in spec


def test_get_vyper_pragma_spec_modern_pep440():
    spec = sources.get_vyper_pragma_spec("#pragma version >=0.4.0,<0.5.0")

    assert Version("0.4.3") in spec
    assert Version("0.3.10") not in spec


def test_get_vyper_pragma_spec_modern_caret_does_not_select_unsupported_pragma_directive():
    spec = sources.get_vyper_pragma_spec("#pragma version ^0.3.0")

    assert Version("0.3.10") in spec
    assert Version("0.3.9") not in spec


def test_get_vyper_pragma_spec_uses_comment_tokens():
    source = """
    MESSAGE: constant(String[32]) = "# @version 0.2.4"
    #pragma optimize gas
    #pragma version ^0.4.0
    """
    spec = sources.get_vyper_pragma_spec(source)

    assert Version("0.4.3") in spec
    assert Version("0.2.4") not in spec


def test_get_vyper_pragma_spec_rejects_duplicate_version_pragmas():
    source = """
    # @version ^0.3.0
    #pragma version ^0.4.0
    """

    with pytest.raises(PragmaError):
        sources.get_vyper_pragma_spec(source)


def test_get_vyper_pragma_spec_rejects_modern_space_separated_ranges():
    with pytest.raises(PragmaError):
        sources.get_vyper_pragma_spec("#pragma version >=0.4.0 <0.5.0")
