#!/usr/bin/python3

import functools

import pytest
from packaging.version import Version

from brownie.exceptions import CompilerError
from brownie.project import build, compiler
from brownie.project.compiler import solidity, vyper


@pytest.fixture
def vyjson(vysource):
    compiler.vyper.set_vyper_version("0.2.4")
    input_json = compiler.generate_input_json({"path.vy": vysource}, language="Vyper")
    yield compiler.compile_from_input_json(input_json)


def test_generate_input_json(vysource):
    input_json = compiler.generate_input_json({"path.vy": vysource}, language="Vyper")
    assert "optimizer" not in input_json["settings"]
    assert input_json["sources"]["path.vy"]["content"] == vysource


def test_generate_input_json_evm(vysource):
    fn = functools.partial(compiler.generate_input_json, {"path.vy": vysource}, language="Vyper")
    assert fn()["settings"]["evmVersion"] == "istanbul"

    all_known_evm_versions = {
        v[0] for v in solidity.EVM_VERSION_MAPPING + vyper.EVM_VERSION_MAPPING
    }
    for evm_version in all_known_evm_versions:
        assert fn(evm_version=evm_version)["settings"]["evmVersion"] == evm_version


def test_compile_input_json(vyjson):
    assert "path" in vyjson["contracts"]["path.vy"]


@pytest.mark.parametrize("vyper_version", ["0.1.0-beta.16", "0.2.4"])
def test_compile_input_json_raises(vyper_version):
    compiler.vyper.set_vyper_version(vyper_version)
    input_json = compiler.generate_input_json({"path.vy": "potato"}, language="Vyper")
    with pytest.raises(CompilerError):
        compiler.compile_from_input_json(input_json)


def test_build_json_keys(vysource):
    build_json = compiler.compile_and_format({"path.vy": vysource})
    assert set(build.BUILD_KEYS) == set(build_json["path"])


def test_dependencies(vysource):
    code = """
# @version 0.2.4
import path as foo
from vyper.interfaces import ERC20
from foo import bar
"""

    build_json = compiler.compile_and_format(
        {"path.vy": vysource, "deps.vy": code, "foo/bar.vy": vysource}
    )
    assert build_json["deps"]["dependencies"] == ["bar", "path"]


def test_compile_empty():
    compiler.compile_and_format({"empty.vy": ""}, vyper_version="0.2.4")


def test_find_vyper_versions_uses_installed_when_available_list_does_not_match(monkeypatch):
    source = {"Foo.vy": "# @version ^0.2.0"}
    monkeypatch.setattr(
        compiler.vyper,
        "_get_vyper_version_list",
        lambda: ([Version("0.1.0")], [Version("0.2.16")]),
    )

    assert compiler.find_vyper_versions(source) == {"0.2.16": ["Foo.vy"]}


def test_set_vyper_version_normalizes_version_like_objects(monkeypatch):
    class LegacyVersion:
        def __str__(self):
            return "0.2.4"

    called = []
    monkeypatch.setattr(compiler.vyper, "_active_version", compiler.vyper.LIB_VYPER_VERSION)
    monkeypatch.setattr(
        compiler.vyper, "_vvm_set_vyper_version", lambda *args, **kwargs: called.append(args)
    )

    assert compiler.vyper.set_vyper_version(LegacyVersion()) == "0.2.4"
    assert called == [(Version("0.2.4"),)]


def test_get_abi():
    code = "@external\ndef baz() -> bool: return True"
    abi = compiler.vyper.get_abi(code, "Vyper")
    assert len(abi) == 1
    assert abi["Vyper"] == [
        {
            "name": "baz",
            "outputs": [{"type": "bool", "name": ""}],
            "inputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
            "gas": 351,
        }
    ]


def test_size_limit(capfd):
    code = f"@external\ndef baz():\n    assert msg.sender != ZERO_ADDRESS, '{'blah'*10000}'"
    compiler.compile_and_format({"foo.vy": code}, vyper_version="0.2.4")
    assert "exceeds EIP-170 limit of 24577" in capfd.readouterr()[0]
