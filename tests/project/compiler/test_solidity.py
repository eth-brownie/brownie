#!/usr/bin/python3

import functools

import pytest
import solcx
from semantic_version import Version

from brownie._config import EVM_EQUIVALENTS
from brownie.exceptions import CompilerError, IncompatibleSolcVersion, PragmaError
from brownie.project import build, compiler


@pytest.fixture
def solc4json(solc4source):
    compiler.set_solc_version("0.4.25")
    input_json = compiler.generate_input_json({"path.sol": solc4source}, True, 200)
    yield compiler.compile_from_input_json(input_json)


@pytest.fixture
def solc5json(solc5source):
    compiler.set_solc_version("0.5.7")
    input_json = compiler.generate_input_json({"path.sol": solc5source}, True, 200)
    yield compiler.compile_from_input_json(input_json)


@pytest.fixture
def solc6json(solc6source):
    compiler.set_solc_version("0.6.2")
    input_json = compiler.generate_input_json({"path.sol": solc6source}, True, 200)
    yield compiler.compile_from_input_json(input_json)


@pytest.fixture
def find_version():
    source = """pragma solidity{};contract Foo {{}}"""

    def fn(version, **kwargs):
        return compiler.find_solc_versions({"Foo": source.format(version)}, **kwargs)

    yield fn


@pytest.fixture
def msolc(monkeypatch):
    installed = [
        Version("0.5.8"),
        Version("0.5.7"),
        Version("0.4.23"),
        Version("0.4.22"),
        Version("0.4.6"),
    ]
    monkeypatch.setattr("solcx.get_installed_solc_versions", lambda: installed)
    monkeypatch.setattr("solcx.install_solc", lambda k, **z: installed.append(k))
    monkeypatch.setattr(
        "solcx.get_installable_solc_versions",
        lambda: [
            Version("0.6.7"),
            Version("0.6.2"),
            Version("0.6.0"),
            Version("0.5.15"),
            Version("0.5.8"),
            Version("0.5.7"),
            Version("0.5.0"),
            Version("0.4.25"),
            Version("0.4.24"),
            Version("0.4.22"),
        ],
    )
    yield installed


def test_set_solc_version():
    compiler.set_solc_version("0.5.7")
    assert solcx.get_solc_version(with_commit_hash=True) == compiler.solidity.get_version()
    assert solcx.get_solc_version(with_commit_hash=True).truncate() == Version("0.5.7")
    compiler.set_solc_version("0.4.25")
    assert solcx.get_solc_version(with_commit_hash=True) == compiler.solidity.get_version()
    assert solcx.get_solc_version(with_commit_hash=True).truncate() == Version("0.4.25")


def test_generate_input_json(solc5source):
    input_json = compiler.generate_input_json({"path.sol": solc5source}, True, 200)
    assert input_json["settings"]["optimizer"]["enabled"] is True
    assert input_json["settings"]["optimizer"]["runs"] == 200
    assert input_json["sources"]["path.sol"]["content"] == solc5source


def test_generate_input_json_evm(solc5source, monkeypatch):
    monkeypatch.setattr("solcx.get_solc_version", lambda **x: Version("0.5.5"))
    fn = functools.partial(compiler.generate_input_json, {"path.sol": solc5source})
    assert fn()["settings"]["evmVersion"] == "petersburg"
    assert fn(evm_version="byzantium")["settings"]["evmVersion"] == "byzantium"
    assert fn(evm_version="petersburg")["settings"]["evmVersion"] == "petersburg"
    monkeypatch.setattr("solcx.get_solc_version", lambda **x: Version("0.5.4"))
    assert fn()["settings"]["evmVersion"] == "byzantium"
    assert fn(evm_version="byzantium")["settings"]["evmVersion"] == "byzantium"
    assert fn(evm_version="petersburg")["settings"]["evmVersion"] == "petersburg"


def test_compile_input_json(solc5json):
    assert "Foo" in solc5json["contracts"]["path.sol"]
    assert "Bar" in solc5json["contracts"]["path.sol"]


def test_compile_input_json_raises():
    input_json = compiler.generate_input_json({"path.sol": "potato"}, True, 200)
    with pytest.raises(CompilerError):
        compiler.compile_from_input_json(input_json)


@pytest.mark.parametrize("original,translated", EVM_EQUIVALENTS.items())
def test_compile_input_json_evm_translates(solc5source, original, translated):
    compiler.set_solc_version("0.5.7")
    input_json = compiler.generate_input_json({"path.sol": solc5source}, True, 200, original)
    compiler.compile_from_input_json(input_json)


def test_build_json_keys(solc5source):
    build_json = compiler.compile_and_format({"path.sol": solc5source})
    assert set(build.BUILD_KEYS) == set(build_json["Foo"])


def test_build_json_unlinked_libraries(solc4source, solc5source, solc6source):
    build_json = compiler.compile_and_format({"path.sol": solc4source}, solc_version="0.4.25")
    assert "__Bar__" in build_json["Foo"]["bytecode"]
    build_json = compiler.compile_and_format({"path.sol": solc5source}, solc_version="0.5.7")
    assert "__Bar__" in build_json["Foo"]["bytecode"]
    build_json = compiler.compile_and_format({"path.sol": solc6source}, solc_version="0.6.2")
    assert "__Bar__" in build_json["Foo"]["bytecode"]


def test_format_link_references(solc4json, solc5json, solc6json):
    evm = solc4json["contracts"]["path.sol"]["Foo"]["evm"]
    assert "__Bar__" in compiler.solidity._format_link_references(evm)
    evm = solc5json["contracts"]["path.sol"]["Foo"]["evm"]
    assert "__Bar__" in compiler.solidity._format_link_references(evm)
    evm = solc6json["contracts"]["path.sol"]["Foo"]["evm"]
    assert "__Bar__" in compiler.solidity._format_link_references(evm)


def test_compiler_errors(solc4source, solc5source):
    with pytest.raises(CompilerError):
        compiler.compile_and_format({"path.sol": solc4source}, solc_version="0.5.7")
    with pytest.raises(CompilerError):
        compiler.compile_and_format({"path.sol": solc5source}, solc_version="0.4.25")


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
        compiler.find_solc_versions({"Foo.sol": "contract Foo {}"})
    with pytest.raises(IncompatibleSolcVersion):
        find_version("^1.0.0", install_needed=False)
    with pytest.raises(IncompatibleSolcVersion):
        find_version("^1.0.0", install_needed=True)


def test_find_solc_versions_install(find_version, msolc):
    assert Version("0.4.25") not in msolc
    assert Version("0.5.10") not in msolc
    find_version("^0.4.24", install_needed=True)
    assert msolc.pop() == Version("0.4.26")
    find_version("^0.4.22", install_latest=True)
    assert msolc.pop() == Version("0.4.26")
    find_version("^0.4.24 || >=0.5.10 <=0.6.7", install_needed=True)
    assert msolc.pop() == Version("0.6.7")
    find_version(">=0.4.24 <=0.6.7", install_latest=True)
    assert msolc.pop() == Version("0.6.7")


def test_install_solc(msolc):
    assert Version("0.5.10") not in msolc
    assert Version("0.6.0") not in msolc
    compiler.install_solc(Version("0.6.0"), Version("0.5.10"))
    assert Version("0.5.10") in msolc
    assert Version("0.6.0") in msolc


def test_first_revert(BrownieTester, ExternalCallTester):
    pc_map = ExternalCallTester._build["pcMap"]
    assert next((i for i in pc_map.values() if "first_revert" in i), False)
    pc_map = BrownieTester._build["pcMap"]
    assert not next((i for i in pc_map.values() if "first_revert" in i), False)


def test_compile_empty():
    compiler.compile_and_format({"empty.sol": ""}, solc_version="0.4.25")


def test_get_abi():
    code = "pragma solidity 0.5.0; contract Foo { function baz() external returns (bool); }"
    abi = compiler.solidity.get_abi(code)
    assert len(abi) == 1
    assert abi["Foo"] == [
        {
            "constant": False,
            "inputs": [],
            "name": "baz",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        }
    ]


def test_size_limit(capfd):
    code = f"""
pragma solidity 0.6.2;
contract Foo {{ function foo() external returns (bool) {{
    require(msg.sender != address(0), "{"blah"*10000}"); }}
}}"""
    compiler.compile_and_format({"foo.sol": code})
    assert "exceeds EIP-170 limit of 24577" in capfd.readouterr()[0]
