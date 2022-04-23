#!/usr/bin/python3

import pytest

from brownie.exceptions import UnsupportedLanguage
from brownie.project import compiler


def test_multiple_compilers(solc4source, vysource):
    compiler.compile_and_format(
        {
            "solc4.sol": solc4source,
            "vyper.vy": vysource,
            "vyperold.vy": "# @version 0.1.0b16\n",
            "solc6.sol": "pragma solidity 0.6.2; contract Foo {}",
        }
    )


def test_multiple_compilers_evm_version_override(solc4source, vysource):
    result = compiler.compile_and_format(
        {
            "solc4.sol": solc4source,
            "vyper.vy": vysource,
            "vyperold.vy": "# @version 0.1.0b16\n",
            "solc6.sol": "pragma solidity 0.6.2; contract Foo {}",
        },
        evm_version={"Solidity": "byzantium", "Vyper": "petersburg"},
    )
    assert result["Bar"]["compiler"]["evm_version"] == "byzantium"
    assert result["vyper"]["compiler"]["evm_version"] == "petersburg"


def test_wrong_suffix():
    with pytest.raises(UnsupportedLanguage):
        compiler.compile_and_format({"foo.bar": ""})


def test_unknown_language():
    with pytest.raises(UnsupportedLanguage):
        compiler.generate_input_json({"foo": ""}, language="Bar")
    with pytest.raises(UnsupportedLanguage):
        compiler.compile_from_input_json({"language": "FooBar"})
    with pytest.raises(UnsupportedLanguage):
        compiler.generate_build_json({"language": "BarBaz"}, {})
