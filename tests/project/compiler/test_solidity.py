#!/usr/bin/python3

import functools

import pytest
import solcx
from semantic_version import Version

from brownie._config import EVM_EQUIVALENTS
from brownie.exceptions import CompilerError, IncompatibleSolcVersion, PragmaError
from brownie.project import build, compiler
from brownie.project.compiler import solidity


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
    """Test that set_solc_version sets the correct solc version."""
    compiler.set_solc_version("0.5.7")
    assert solcx.get_solc_version(with_commit_hash=True) == compiler.solidity.get_version()
    assert solcx.get_solc_version(with_commit_hash=True).truncate() == Version("0.5.7")
    compiler.set_solc_version("0.4.25")
    assert solcx.get_solc_version(with_commit_hash=True) == compiler.solidity.get_version()
    assert solcx.get_solc_version(with_commit_hash=True).truncate() == Version("0.4.25")


def test_generate_input_json(solc5source):
    """Test that generate_input_json produces correct optimizer and source settings."""
    input_json = compiler.generate_input_json({"path.sol": solc5source}, True, 200)
    assert input_json["settings"]["optimizer"]["enabled"] is True
    assert input_json["settings"]["optimizer"]["runs"] == 200
    assert input_json["sources"]["path.sol"]["content"] == solc5source


def test_generate_input_json_evm(solc5source, monkeypatch):
    """Test that generate_input_json sets correct evmVersion based on solc version and input."""
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
    """Test that compile_from_input_json compiles contracts and includes expected names."""
    assert "Foo" in solc5json["contracts"]["path.sol"]
    assert "Bar" in solc5json["contracts"]["path.sol"]


def test_compile_input_json_raises():
    """Test that compile_from_input_json raises CompilerError on invalid input."""
    input_json = compiler.generate_input_json({"path.sol": "potato"}, True, 200)
    with pytest.raises(CompilerError):
        compiler.compile_from_input_json(input_json)


@pytest.mark.parametrize("original,translated", EVM_EQUIVALENTS.items())
def test_compile_input_json_evm_translates(solc5source, original, translated):
    """Test that EVM_EQUIVALENTS are translated correctly in input JSON."""
    compiler.set_solc_version("0.5.7")
    input_json = compiler.generate_input_json({"path.sol": solc5source}, True, 200, original)
    compiler.compile_from_input_json(input_json)


def test_build_json_keys(solc5source):
    """Test that build_json contains all required build keys."""
    build_json = compiler.compile_and_format({"path.sol": solc5source})
    assert set(build.BUILD_KEYS) == set(build_json["Foo"])


def test_build_json_unlinked_libraries(solc4source, solc5source, solc6source):
    """Test that unlinked libraries are present in bytecode for various solc versions."""
    build_json = compiler.compile_and_format({"path.sol": solc4source}, solc_version="0.4.25")
    assert "__Bar__" in build_json["Foo"]["bytecode"]
    build_json = compiler.compile_and_format({"path.sol": solc5source}, solc_version="0.5.7")
    assert "__Bar__" in build_json["Foo"]["bytecode"]
    build_json = compiler.compile_and_format({"path.sol": solc6source}, solc_version="0.6.2")
    assert "__Bar__" in build_json["Foo"]["bytecode"]


def test_format_link_references(solc4json, solc5json, solc6json):
    """Test that _format_link_references correctly formats unlinked libraries in bytecode."""
    evm = solc4json["contracts"]["path.sol"]["Foo"]["evm"]
    assert "__Bar__" in compiler.solidity._format_link_references(evm)
    evm = solc5json["contracts"]["path.sol"]["Foo"]["evm"]
    assert "__Bar__" in compiler.solidity._format_link_references(evm)
    evm = solc6json["contracts"]["path.sol"]["Foo"]["evm"]
    assert "__Bar__" in compiler.solidity._format_link_references(evm)


def test_compiler_errors(solc4source, solc5source):
    """Test that compile_and_format raises CompilerError for incompatible solc versions."""
    with pytest.raises(CompilerError):
        compiler.compile_and_format({"path.sol": solc4source}, solc_version="0.5.7")
    with pytest.raises(CompilerError):
        compiler.compile_and_format({"path.sol": solc5source}, solc_version="0.4.25")


def test_min_version():
    """Test that set_solc_version raises IncompatibleSolcVersion for too-old versions."""
    with pytest.raises(IncompatibleSolcVersion):
        compiler.set_solc_version("v0.4.21")


def test_find_solc_versions(find_version, msolc):
    """Test that find_solc_versions selects correct versions and raises on errors."""
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
    """Test that find_solc_versions can install new versions as needed."""
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
    """Test that install_solc installs the requested solc versions."""
    assert Version("0.5.10") not in msolc
    assert Version("0.6.0") not in msolc
    compiler.install_solc(Version("0.6.0"), Version("0.5.10"))
    assert Version("0.5.10") in msolc
    assert Version("0.6.0") in msolc


def test_first_revert(BrownieTester, ExternalCallTester):
    """Test that first_revert is set only for ExternalCallTester, not BrownieTester."""
    pc_map = ExternalCallTester._build["pcMap"]
    assert next((i for i in pc_map.values() if "first_revert" in i), False)
    pc_map = BrownieTester._build["pcMap"]
    assert not next((i for i in pc_map.values() if "first_revert" in i), False)


def test_compile_empty():
    """Test that compile_and_format does not fail on empty source."""
    compiler.compile_and_format({"empty.sol": ""}, solc_version="0.4.25")


def test_get_abi():
    """Test that get_abi returns the correct ABI for a simple contract."""
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
    """Test that compile_and_format warns when contract size exceeds EIP-170 limit."""
    code = f"""
pragma solidity 0.6.2;
contract Foo {{ function foo() external returns (bool) {{
    require(msg.sender != address(0), "{"blah"*10000}"); }}
}}"""
    compiler.compile_and_format({"foo.sol": code})
    assert "exceeds EIP-170 limit of 24577" in capfd.readouterr()[0]


def test__remove_metadata():
    """Test that _remove_metadata strips metadata from bytecode and handles edge cases."""
    bytecode = "6001600055" + "aabbccddeeff" * 2 + "000a"
    result = solidity._remove_metadata(bytecode)
    expected = bytecode[:-(int("000a", 16) + 2) * 2]
    assert result == expected
    assert solidity._remove_metadata("") == ""
    short_bytecode = "6001600055"
    assert solidity._remove_metadata(short_bytecode) == ""

def test__get_solc_version_list():
    """Test that _get_solc_version_list returns available and installed solc versions."""
    available, installed = solidity._get_solc_version_list()
    assert isinstance(available, list) and all(isinstance(v, Version) for v in available), available
    assert isinstance(installed, list) and all(isinstance(v, Version) for v in installed), installed

def test__get_unique_build_json_multiple_deps_and_fallback():
    """Test _get_unique_build_json with multiple dependencies and fallback contract."""
    class DummyDep:
        def __init__(self, contract_id, name):
            self.contract_id = contract_id
            self.name = name
            self.nodeType = "ContractDefinition"
            self.offset = (0, 10)
            self.contractKind = "contract"
            self.dependencies = []
        def parent(self):
            class Parent:
                absolutePath = f"{self.name}.sol"
                name = self.name
                nodeType = "SourceUnit"
            return Parent()
    class DummyNode(DummyDep):
        def __init__(self):
            super().__init__(1, "Main")
            self.dependencies = [DummyDep(2, "DepA"), DummyDep(3, "DepB")]
            self.contractKind = "contract"
            self.offset = (0, 10)
    dummy_node = DummyNode()
    output_evm = {
        "bytecode": {"object": "6001600055", "linkReferences": {}},
        "deployedBytecode": {"object": "6001600055", "sourceMap": "0:10:1:-", "opcodes": "PUSH1 0x01 PUSH1 0x00 SSTORE", "linkReferences": {}}
    }
    stmt_nodes = {"1": set(), "2": set(), "3": set()}
    branch_nodes = {"1": set(), "2": set(), "3": set()}
    build_json = solidity._get_unique_build_json(output_evm, dummy_node, stmt_nodes, branch_nodes, True)
    assert "bytecode" in build_json
    assert "pcMap" in build_json
    assert "coverageMap" in build_json
    assert "dependencies" in build_json
    assert len(build_json["dependencies"]) == 2

def test__generate_coverage_data_optimizer_revert_and_branches():
    """Test _generate_coverage_data with optimizer_revert and branch/statement logic."""
    class DummyNode:
        def __init__(self):
            self.contract_id = 1
            self.dependencies = []
            self.name = "Dummy"
            self.contractKind = "contract"
            self.offset = (0, 10)
        def parent(self):
            class Parent:
                absolutePath = "Dummy.sol"
                name = "Dummy"
                nodeType = "SourceUnit"
            return Parent()
        def children(self, *args, **kwargs):
            # Simulate a function node with a revert/require
            class FnNode:
                nodeType = "FunctionDefinition"
                name = "foo"
                offset = (0, 10)
                def children(self, **kwargs):
                    class RevertNode:
                        nodeType = "FunctionCall"
                        expression = type("Expr", (), {"name": "revert"})
                        arguments = [1, 2]
                        offset = (0, 10)
                    return [RevertNode()]
            return [FnNode()]
    dummy_node = DummyNode()
    stmt_nodes = {"1": set([(0, 10)])}
    branch_nodes = {"1": set()}
    # Simulate source map and opcodes that will trigger optimizer_revert logic
    pc_map, statement_map, branch_map = solidity._generate_coverage_data(
        "0:10:1:-", "PUSH1 0x01 PUSH1 0x00 SSTORE REVERT", dummy_node, stmt_nodes, branch_nodes, False, 5
    )
    assert isinstance(pc_map, dict)
    assert isinstance(statement_map, dict)
    assert isinstance(branch_map, dict)

def test__generate_coverage_data_source_map_trimming():
    """Test _generate_coverage_data with a source map that requires trimming (YUL optimizer)."""
    class DummyNode:
        def __init__(self):
            self.contract_id = 1
            self.dependencies = []
            self.name = "Dummy"
            self.contractKind = "contract"
            self.offset = (0, 10)
        def parent(self):
            class Parent:
                absolutePath = "Dummy.sol"
                name = "Dummy"
                nodeType = "SourceUnit"
            return Parent()
        def children(self, *args, **kwargs):
            return []
    dummy_node = DummyNode()
    stmt_nodes = {"1": set()}
    branch_nodes = {"1": set()}
    # The last entry in the source map has contract_id -1, which should be trimmed
    pc_map, statement_map, branch_map = solidity._generate_coverage_data(
        "0:10:1:-;0:10:-1:-", "PUSH1 0x01 PUSH1 0x00 SSTORE", dummy_node, stmt_nodes, branch_nodes, False, 3
    )
    assert isinstance(pc_map, dict)

def test__generate_coverage_data_revert_map():
    """Test _generate_coverage_data with revert/require statements to exercise revert_map logic."""
    class DummyNode:
        def __init__(self):
            self.contract_id = 1
            self.dependencies = []
            self.name = "Dummy"
            self.contractKind = "contract"
            self.offset = (0, 10)
        def parent(self):
            class Parent:
                absolutePath = "Dummy.sol"
                name = "Dummy"
                nodeType = "SourceUnit"
            return Parent()
        def children(self, *args, **kwargs):
            class FnNode:
                nodeType = "FunctionDefinition"
                name = "foo"
                offset = (0, 10)
                def children(self, **kwargs):
                    class RevertNode:
                        nodeType = "FunctionCall"
                        expression = type("Expr", (), {"name": "require"})
                        arguments = [1, 2]
                        offset = (0, 10)
                    return [RevertNode()]
            return [FnNode()]
    dummy_node = DummyNode()
    stmt_nodes = {"1": set([(0, 10)])}
    branch_nodes = {"1": set()}
    pc_map, statement_map, branch_map = solidity._generate_coverage_data(
        "0:10:1:-", "PUSH1 0x01 PUSH1 0x00 SSTORE REVERT", dummy_node, stmt_nodes, branch_nodes, False, 5
    )
    assert isinstance(pc_map, dict)

def test__find_revert_offset_all_branches():
    """Test _find_revert_offset for all code paths (CALLVALUE, function selector, next_offset, final revert)."""
    # CALLVALUE branch
    pc_list = [{"op": "CALLVALUE"}, {}, {}, {}, {}, {}, {}, {}, {"op": "REVERT"}]
    source_map = [[0, 10, 1, "-"]]
    solidity._find_revert_offset(pc_list, source_map, None, None, None)
    # function selector table (no fn_node)
    solidity._find_revert_offset([], [], None, None, None)
    # next_offset branch
    class DummyFnNode:
        offset = (0, 10)
        def __getitem__(self, idx):
            class ExprStmt:
                nodeType = "ExpressionStatement"
                expression = type("Expr", (), {"nodeType": "FunctionCall", "expression": type("E", (), {"name": "revert"}), "offset": 5})
            return ExprStmt()
        def __len__(self):
            return 1
    class DummySourceNode:
        contract_id = 1
    solidity._find_revert_offset([], [[0, 10, 1, "-"]], DummySourceNode(), DummyFnNode(), "foo")

def test__set_invalid_error_string_modulus_and_default():
    """Test _set_invalid_error_string for modulus by zero and default (no dev string)."""
    class DummyNodeMod:
        def children(self, **kwargs):
            class Node:
                nodeType = "BinaryOperation"
                operator = "%"
                offset = (0, 1)
            return [Node()]
    pc_map = {"offset": (0, 1)}
    solidity._set_invalid_error_string(DummyNodeMod(), pc_map)
    assert pc_map["dev"] == "Modulus by zero"

    class DummyNodeDefault:
        def children(self, **kwargs):
            class Node:
                nodeType = "Other"
                offset = (0, 1)
            return [Node()]
    pc_map2 = {"offset": (0, 1)}
    solidity._set_invalid_error_string(DummyNodeDefault(), pc_map2)
    assert "dev" not in pc_map2


@pytest.mark.parametrize(
    "fn_node_attrs,expected_name",
    [
        ({"name": None, "kind": "function", "isConstructor": False}, "<fallback>"),
        ({"name": None, "kind": "function", "isConstructor": True}, "<constructor>"),
        ({"name": None, "kind": "special", "isConstructor": False}, "<special>"),
    ],
)
def test__get_active_fn(fn_node_attrs, expected_name):
    """Test _get_active_fn for fallback, constructor, and non-function kind."""
    class DummyFnNode:
        def __init__(self, attrs):
            for k, v in attrs.items():
                setattr(self, k, v)
        def parent(self):
            class Parent:
                nodeType = "SourceUnit"
                name = "Dummy"
            return Parent()
    class DummySourceNode:
        def children(self, **kwargs):
            return [DummyFnNode(fn_node_attrs)]
    _, name = solidity._get_active_fn(DummySourceNode(), (0, 1))
    assert name == expected_name

@pytest.mark.parametrize(
    "node_type,extra_setup",
    [
        ("IfStatement", lambda n: setattr(n, "condition", n)),
        ("Conditional", lambda n: setattr(n, "condition", n)),
        ("BinaryOperation", lambda n: [setattr(n, "condition", n), setattr(n, "leftExpression", n), setattr(n, "rightExpression", n)]),
        ("UnaryOperation", lambda n: [setattr(n, "condition", n), setattr(n, "subExpression", n)]),
        ("NestedBinaryOperation", lambda n: [setattr(n, "condition", n), setattr(n, "leftExpression", n), setattr(n, "rightExpression", n), setattr(n, "children", lambda *a, **k: [n])]),
    ],
)
def test__get_recursive_branches(node_type, extra_setup):
    """Test _get_recursive_branches for various node types and nested."""

    class DummyNode:
        def __init__(self, node_type):
            self.nodeType = node_type if node_type != "NestedBinaryOperation" else "BinaryOperation"
        def children(self, include_parents=True, include_self=True, filters=None):
            return []
        def is_child_of(self, other):
            return False
    node = DummyNode(node_type)
    extra_setup(node)
    result = solidity._get_recursive_branches(node)
    assert isinstance(result, set)
