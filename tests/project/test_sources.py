#!/usr/bin/python3

import pytest
from semantic_version import NpmSpec

from brownie.exceptions import NamespaceCollision
from brownie.project import sources

MESSY_SOURCE = """
  pragma  solidity>=0.4.22    <0.7.0  ;contract Foo{} interface Bar {}
abstract contract Baz is Foo {}
 library   Potato{}"""


@pytest.fixture(scope="module")
def sourceobj(solc5source):
    yield sources.Sources(
        {"path/to/Foo.sol": solc5source}, {"interfaces/Baz.vy": "@external\ndef bar(): pass"}
    )


def test_namespace_collisions(solc5source):
    # contract collision
    with pytest.raises(NamespaceCollision):
        sources.Sources({"foo.sol": solc5source, "bar.sol": solc5source}, {})
    # contract / interface collision
    with pytest.raises(NamespaceCollision):
        sources.Sources({"foo.sol": solc5source}, {"bar.sol": solc5source})
    # interface collision
    with pytest.raises(NamespaceCollision):
        sources.Sources({}, {"foo.sol": solc5source, "bar.sol": solc5source})
    # solc / vyper collision
    with pytest.raises(NamespaceCollision):
        sources.Sources({"foo.sol": solc5source, "Foo.vy": "@external\ndef bar(): pass"}, {})
    with pytest.raises(NamespaceCollision):
        sources.Sources({"foo.sol": solc5source}, {"Foo.vy": "@external\ndef bar(): pass"})


def test_get_path_list(sourceobj):
    assert sourceobj.get_path_list() == ["interfaces/Baz.vy", "path/to/Foo.sol"]


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
    assert names == ["Foo", "Bar", "Baz", "Potato"]


def test_get_pragma_spec():
    assert sources.get_pragma_spec(MESSY_SOURCE) == NpmSpec(">=0.4.22 <0.7.0")
