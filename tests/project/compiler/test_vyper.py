#!/usr/bin/python3

import functools

import pytest

from brownie.exceptions import CompilerError
from brownie.project import build, compiler
from brownie.project.compiler import solidity, vyper


@pytest.fixture
def vyjson(vysource):
    """Fixture to compile a Vyper source and yield the result."""
    compiler.vyper.set_vyper_version("0.2.4")
    input_json = compiler.generate_input_json({"path.vy": vysource}, language="Vyper")
    yield compiler.compile_from_input_json(input_json)


def test_generate_input_json(vysource):
    """Test that generate_input_json for Vyper omits optimizer and includes source."""
    input_json = compiler.generate_input_json({"path.vy": vysource}, language="Vyper")
    assert "optimizer" not in input_json["settings"]
    assert input_json["sources"]["path.vy"]["content"] == vysource


def test_generate_input_json_evm(vysource):
    """Test that generate_input_json sets correct evmVersion for Vyper."""
    fn = functools.partial(compiler.generate_input_json, {"path.vy": vysource}, language="Vyper")
    assert fn()["settings"]["evmVersion"] == "istanbul"

    all_known_evm_versions = {
        v[0] for v in solidity.EVM_VERSION_MAPPING + vyper.EVM_VERSION_MAPPING
    }
    for evm_version in all_known_evm_versions:
        assert fn(evm_version=evm_version)["settings"]["evmVersion"] == evm_version


def test_compile_input_json(vyjson):
    """Test that compile_from_input_json compiles Vyper contracts and includes expected names."""
    assert "path" in vyjson["contracts"]["path.vy"]


@pytest.mark.parametrize("vyper_version", ["0.1.0-beta.16", "0.2.4"])
def test_compile_input_json_raises(vyper_version):
    """Test that compile_from_input_json raises CompilerError on invalid Vyper input."""
    compiler.vyper.set_vyper_version(vyper_version)
    input_json = compiler.generate_input_json({"path.vy": "potato"}, language="Vyper")
    with pytest.raises(CompilerError):
        compiler.compile_from_input_json(input_json)


def test_build_json_keys(vysource):
    """Test that build_json contains all required build keys for Vyper."""
    build_json = compiler.compile_and_format({"path.vy": vysource})
    assert set(build.BUILD_KEYS) == set(build_json["path"])


def test_dependencies(vysource):
    """Test that dependencies are correctly extracted from Vyper AST."""
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
    """Test that compile_and_format does not fail on empty Vyper source."""
    compiler.compile_and_format({"empty.vy": ""}, vyper_version="0.2.4")


def test_get_abi():
    """Test that get_abi returns the correct ABI for a simple Vyper contract."""
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
    """Test that compile_and_format warns when Vyper contract size exceeds EIP-170 limit."""
    code = f"@external\ndef baz():\n    assert msg.sender != ZERO_ADDRESS, '{'blah'*10000}'"
    compiler.compile_and_format({"foo.vy": code}, vyper_version="0.2.4")
    assert "exceeds EIP-170 limit of 24577" in capfd.readouterr()[0]


def test__get_vyper_version_list():
    """Test that _get_vyper_version_list returns available and installed vyper versions."""
    available, installed = vyper._get_vyper_version_list()
    assert isinstance(available, list)
    assert isinstance(installed, list)
    if installed:
        from brownie._c_constants import Version
        assert all(isinstance(v, Version) for v in installed)
    if available:
        from brownie._c_constants import Version
        assert all(isinstance(v, Version) for v in available)


def test__get_unique_build_json_complex_ast():
    """Test _get_unique_build_json with complex AST and multiple dependencies."""
    output_evm = {
        "bytecode": {"object": "6001600055", "linkReferences": {}},
        "deployedBytecode": {"object": "6001600055", "sourceMap": "0:10:1:-", "opcodes": "PUSH1 0x01 PUSH1 0x00 SSTORE", "linkReferences": {}}
    }
    ast_json = {
        "body": [
            {"ast_type": "Import", "name": "foo.vy"},
            {"ast_type": "ImportFrom", "name": "bar.vy", "module": "baz"},
            {"ast_type": "ImportFrom", "name": "should_skip", "module": "vyper.interfaces"},
            {"ast_type": "FunctionDef", "name": "main", "src": "0:10"},
        ]
    }
    build_json = vyper._get_unique_build_json(output_evm, "Dummy.vy", "Dummy", ast_json, (0, 10))
    assert "bytecode" in build_json
    assert "pcMap" in build_json
    assert "coverageMap" in build_json
    assert "dependencies" in build_json
    assert build_json["dependencies"] == ["bar", "foo"]


def test__generate_coverage_data_real_opcodes_and_ast():
    """Test _generate_coverage_data with real opcodes and AST for branch/statement coverage."""
    ast_json = [
        {"ast_type": "FunctionDef", "name": "main", "src": "0:10"},
        {"ast_type": "If", "src": "0:5", "test": {"src": "0:2"}, "body": [], "orelse": []},
    ]
    # Simulate opcodes and source map for coverage
    pc_map, statement_map, branch_map = vyper._generate_coverage_data(
        "0:10:1:-;0:5:1:-", "PUSH1 0x01 JUMPI PUSH1 0x00 SSTORE", "Dummy", ast_json
    )
    assert isinstance(pc_map, dict)
    assert isinstance(statement_map, dict)
    assert isinstance(branch_map, dict)


@pytest.mark.parametrize(
    "ast_json,offset,expected",
    [
        ([], (0, 1), None),
        ([{"src": "0:1", "ast_type": "FunctionDef"}], (0, 1), {"src": "0:1", "ast_type": "FunctionDef"}),
        (
            [
                {
                    "src": "0:1",
                    "ast_type": "FunctionDef",
                    "body": [
                        {"src": "0:1", "ast_type": "Expr"}
                    ]
                }
            ],
            (0, 1),
            {"src": "0:1", "ast_type": "FunctionDef"},
        ),
    ],
)
def test__find_node_by_offset(ast_json, offset, expected):
    """Test _find_node_by_offset with recursion and matching offsets."""
    result = vyper._find_node_by_offset(ast_json, offset)
    if expected is None:
        assert result is None
    else:
        assert isinstance(result, dict)
        assert result["src"] == expected["src"]


@pytest.mark.parametrize(
    "ast_json,expected_len",
    [
        ([{"src": "0:1", "ast_type": "FunctionDef"}], 1),
        ([{"src": "0:1", "ast_type": "FunctionDef", "body": [{"src": "0:2", "ast_type": "Expr"}]}], 2),
        ([], 0),
    ],
)
def test__get_statement_nodes(ast_json, expected_len):
    """Test _get_statement_nodes with nested ASTs and no children."""
    result = vyper._get_statement_nodes(ast_json)
    assert isinstance(result, list)
    assert len(result) == expected_len


def test__convert_to_semver_empty():
    """Test _convert_to_semver with empty input list."""
    result = vyper._convert_to_semver([])
    assert result == []


def test__get_dependencies():
    """Test that _get_dependencies returns sorted contract names from AST."""
    ast_json = [
        {"ast_type": "Import", "name": "foo.vy"},
        {"ast_type": "ImportFrom", "name": "bar.vy", "module": "baz"},
        {"ast_type": "ImportFrom", "name": "should_skip", "module": "vyper.interfaces"},
    ]
    result = vyper._get_dependencies(ast_json)
    assert result == ["bar", "foo"]


def test__is_revert_jump():
    """Test that _is_revert_jump returns True only for JUMPI with correct value."""
    pc_list = [{"op": "JUMPI"}, {"op": "PUSH1", "value": "0x10"}]
    assert not vyper._is_revert_jump(pc_list, 16)
    pc_list = [{"op": "JUMPI"}, {"op": "PUSH1", "value": "0x10"}]
    pc_list[-1]["op"] = "JUMPI"
    pc_list[-2]["value"] = "0x10"
    assert vyper._is_revert_jump(pc_list, 16) is True


def test__generate_coverage_data_minimal():
    """Test that _generate_coverage_data returns correct types for minimal input."""
    ast_json = []
    pc_map, statement_map, branch_map = vyper._generate_coverage_data(
        "0:10:1:-", "PUSH1 0x01 PUSH1 0x00 SSTORE", "Dummy", ast_json
    )
    assert isinstance(pc_map, dict)
    assert isinstance(statement_map, dict)
    assert isinstance(branch_map, dict)


def test__convert_src():
    """Test that _convert_src parses src strings and handles None."""
    assert vyper._convert_src("10:5") == (10, 15)
    assert vyper._convert_src(None) == (-1, -1)
