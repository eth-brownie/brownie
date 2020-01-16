#!/usr/bin/python3

import json

import pytest
from semantic_version import NpmSpec

from brownie.exceptions import NamespaceCollision
from brownie.project import compile_source, sources

MESSY_SOURCE = """
  pragma  solidity>=0.4.22    <0.7.0  ;contract Foo{} interface Bar {}
abstract contract Baz is Foo {}
 library   Potato{}"""


@pytest.fixture(scope="module")
def sourceobj(solc5source):
    yield sources.Sources(
        {"path/to/Foo.sol": solc5source}, {"interfaces/Baz.vy": "@public\ndef bar(): pass"}
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
        sources.Sources({"foo.sol": solc5source, "Foo.vy": "@public\ndef bar(): pass"}, {})
    with pytest.raises(NamespaceCollision):
        sources.Sources({"foo.sol": solc5source}, {"Foo.vy": "@public\ndef bar(): pass"})


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


def test_expand_offset(btsource, BrownieTester):
    minified, _ = sources.minify(btsource)
    expanded = BrownieTester._project._sources.expand_offset(
        "BrownieTester", (minified.index("contract"), minified.index("contract") + 7)
    )
    assert btsource.index("contract"), btsource.index("contract") + 7 == expanded


def test_minify_solc(solc5source):
    foo = compile_source(solc5source, solc_version="0.5.7")["Foo"]
    minified, _ = sources.minify(solc5source)
    minifoo = compile_source(minified, solc_version="0.5.7")["Foo"]
    assert foo._build["bytecodeSha1"] == minifoo._build["bytecodeSha1"]
    assert foo._build["source"] != minifoo._build["source"]


def test_minify_vyper():
    code = "@public\ndef foo(a: address) -> bool:    return True\n\n"
    foo = compile_source(code)["Vyper"]
    minified, _ = sources.minify(code, "Vyper")
    minifoo = compile_source(minified)["Vyper"]
    assert foo._build["bytecodeSha1"] == minifoo._build["bytecodeSha1"]
    assert foo._build["source"] != minifoo._build["source"]


def test_minify_json():
    foo_list = [{"foo": "bar"}, {"baz": "potato"}]
    foo = json.dumps(foo_list)
    minifoo, _ = sources.minify(foo, "json")
    assert foo != minifoo
    assert json.loads(minifoo) == foo_list


def test_get_contracts():
    contracts = sources.get_contracts(MESSY_SOURCE)
    assert len(contracts) == 4
    assert contracts["Foo"] == "contract Foo{}"
    assert contracts["Bar"] == "interface Bar {}"
    assert contracts["Baz"] == "abstract contract Baz is Foo {}"
    assert contracts["Potato"] == "library   Potato{}"


def test_get_pragma_spec():
    assert sources.get_pragma_spec(MESSY_SOURCE) == NpmSpec(">=0.4.22 <0.7.0")
