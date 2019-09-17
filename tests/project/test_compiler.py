#!/usr/bin/python3

import functools
import pytest
from semantic_version import Version
import solcx

from brownie.project import compiler, build
from brownie.exceptions import CompilerError, IncompatibleSolcVersion, PragmaError


@pytest.fixture
def solc4json(solc4source):
    compiler.set_solc_version("0.4.25")
    input_json = compiler.generate_input_json({"path": solc4source}, True, 200)
    yield compiler.compile_from_input_json(input_json)


@pytest.fixture
def solc5json(solc5source):
    compiler.set_solc_version("0.5.7")
    input_json = compiler.generate_input_json({"path": solc5source}, True, 200)
    yield compiler.compile_from_input_json(input_json)


@pytest.fixture
def find_version():
    source = """pragma solidity{};contract Foo {{}}"""

    def fn(version, **kwargs):
        return compiler.find_solc_versions({"Foo": source.format(version)}, **kwargs)

    yield fn


@pytest.fixture
def msolc(monkeypatch):
    installed = ["v0.5.8", "v0.5.7", "v0.4.23", "v0.4.22", "v0.4.6"]
    monkeypatch.setattr("solcx.get_installed_solc_versions", lambda: installed)
    monkeypatch.setattr("solcx.install_solc", lambda k: installed.append("v" + k))
    yield installed


def test_set_solc_version():
    compiler.set_solc_version("0.5.7")
    assert "0.5.7" in solcx.get_solc_version_string()
    compiler.set_solc_version("0.4.25")
    assert "0.4.25" in solcx.get_solc_version_string()


def test_generate_input_json(solc5source):
    input_json = compiler.generate_input_json({"path": solc5source}, True, 200)
    assert input_json["settings"]["optimizer"]["enabled"] is True
    assert input_json["settings"]["optimizer"]["runs"] == 200
    assert input_json["sources"]["path"]["content"] == solc5source
    input_json = compiler.generate_input_json(
        {"path": solc5source}, optimize=False, runs=0, minify=True
    )
    assert input_json["settings"]["optimizer"]["enabled"] is False
    assert input_json["settings"]["optimizer"]["runs"] == 0
    assert input_json["sources"]["path"]["content"] != solc5source


def test_generate_input_json_evm(solc5source, monkeypatch):
    monkeypatch.setattr("solcx.get_solc_version", lambda: Version("0.5.5"))
    fn = functools.partial(compiler.generate_input_json, {"path": solc5source})
    assert fn()["settings"]["evmVersion"] == "petersburg"
    assert fn(evm_version="byzantium")["settings"]["evmVersion"] == "byzantium"
    assert fn(evm_version="petersburg")["settings"]["evmVersion"] == "petersburg"
    monkeypatch.setattr("solcx.get_solc_version", lambda: Version("0.5.4"))
    assert fn()["settings"]["evmVersion"] == "byzantium"
    assert fn(evm_version="byzantium")["settings"]["evmVersion"] == "byzantium"
    assert fn(evm_version="petersburg")["settings"]["evmVersion"] == "petersburg"


def test_compile_input_json(solc5json):
    assert "Foo" in solc5json["contracts"]["path"]
    assert "Bar" in solc5json["contracts"]["path"]


def test_compile_input_json_raises():
    input_json = compiler.generate_input_json({"path": "potato"}, True, 200)
    with pytest.raises(CompilerError):
        compiler.compile_from_input_json(input_json)


def test_compile_optimizer(monkeypatch):
    def _test_compiler(a, **kwargs):
        assert kwargs["optimize"] is True
        assert kwargs["optimize_runs"] == 666

    monkeypatch.setattr("solcx.compile_standard", _test_compiler)
    input_json = {"settings": {"optimizer": {"enabled": True, "runs": 666}}}
    compiler.compile_from_input_json(input_json)
    input_json = {"settings": {"optimizer": {"enabled": True, "runs": 31337}}}
    with pytest.raises(AssertionError):
        compiler.compile_from_input_json(input_json)
    input_json = {"settings": {"optimizer": {"enabled": False, "runs": 666}}}
    with pytest.raises(AssertionError):
        compiler.compile_from_input_json(input_json)


def test_build_json_keys(solc5source):
    build_json = compiler.compile_and_format({"path": solc5source})
    assert set(build.BUILD_KEYS) == set(build_json["Foo"])


def test_build_json_unlinked_libraries(solc4source, solc5source):
    build_json = compiler.compile_and_format(
        {"path": solc5source}, solc_version="0.5.7"
    )
    assert "__Bar__" in build_json["Foo"]["bytecode"]
    build_json = compiler.compile_and_format(
        {"path": solc4source}, solc_version="0.4.25"
    )
    assert "__Bar__" in build_json["Foo"]["bytecode"]


def test_format_link_references(solc4json, solc5json):
    evm = solc5json["contracts"]["path"]["Foo"]["evm"]
    assert "__Bar__" in compiler._format_link_references(evm)
    evm = solc4json["contracts"]["path"]["Foo"]["evm"]
    assert "__Bar__" in compiler._format_link_references(evm)


def test_compiler_errors(solc4source, solc5source):
    with pytest.raises(CompilerError):
        compiler.compile_and_format({"path": solc4source}, solc_version="0.5.7")
    with pytest.raises(CompilerError):
        compiler.compile_and_format({"path": solc5source}, solc_version="0.4.25")


def test_min_version():
    with pytest.raises(IncompatibleSolcVersion):
        compiler.set_solc_version("v0.4.21")


def test_find_solc_versions(find_version, msolc):
    assert "0.4.22" in find_version("0.4.22")
    assert "0.4.23" in find_version("^0.4.20")
    assert "0.5.8" in find_version(">0.4.20")
    assert "0.5.8" in find_version("<=0.5.8")
    assert "0.5.7" in find_version(">=0.4.2 <0.5.8")
    assert "0.5.7" in find_version(">0.4.8 <0.5.8 || 0.5.11")
    assert "0.4.22" in find_version("0.5.9 || 0.4.22")
    with pytest.raises(PragmaError):
        compiler.find_solc_versions({"Foo": "contract Foo {}"})
    with pytest.raises(IncompatibleSolcVersion):
        find_version("^0.6.0", install_needed=False)
    with pytest.raises(PragmaError):
        find_version("^0.6.0", install_needed=True)


def test_find_solc_versions_install(find_version, msolc):
    assert "v0.4.25" not in msolc
    assert "v0.5.10" not in msolc
    find_version("^0.4.24", install_needed=True)
    assert msolc.pop() == "v0.4.25"
    find_version("^0.4.22", install_latest=True)
    assert msolc.pop() == "v0.4.25"
    find_version("^0.4.24 || >=0.5.10", install_needed=True)
    assert msolc.pop() == "v0.5.10"
    find_version(">=0.4.24", install_latest=True)
    assert msolc.pop() == "v0.5.10"


def test_install_solc(msolc):
    assert "v0.5.10" not in msolc
    assert "v0.6.0" not in msolc
    compiler.install_solc("0.6.0", "0.5.10")
    assert "v0.5.10" in msolc
    assert "v0.6.0" in msolc


def test_first_revert(BrownieTester, ExternalCallTester):
    pc_map = ExternalCallTester._build["pcMap"]
    assert next((i for i in pc_map.values() if "first_revert" in i), False)
    pc_map = BrownieTester._build["pcMap"]
    assert not next((i for i in pc_map.values() if "first_revert" in i), False)
