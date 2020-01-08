#!/usr/bin/python3

import functools

import pytest
import vyper
from semantic_version import Version
from vyper.exceptions import StructureException

from brownie.project import build, compiler


@pytest.fixture
def vyjson(vysource):
    input_json = compiler.generate_input_json({"path.vy": vysource}, language="Vyper")
    yield compiler.compile_from_input_json(input_json)


def test_version():
    assert compiler.vyper.get_version() == Version.coerce(vyper.__version__)


def test_generate_input_json(vysource):
    input_json = compiler.generate_input_json({"path.vy": vysource}, minify=False, language="Vyper")
    assert "optimizer" not in input_json["settings"]
    assert input_json["sources"]["path.vy"]["content"] == vysource
    input_json = compiler.generate_input_json({"path.vy": vysource}, minify=True, language="Vyper")
    assert "optimizer" not in input_json["settings"]
    assert input_json["sources"]["path.vy"]["content"] != vysource


def test_generate_input_json_evm(vysource):
    fn = functools.partial(compiler.generate_input_json, {"path.vy": vysource}, language="Vyper")
    assert fn()["settings"]["evmVersion"] == "petersburg"
    assert fn(evm_version="byzantium")["settings"]["evmVersion"] == "byzantium"
    assert fn(evm_version="petersburg")["settings"]["evmVersion"] == "petersburg"


def test_compile_input_json(vyjson):
    assert "path" in vyjson["contracts"]["path.vy"]


def test_compile_input_json_raises():
    input_json = compiler.generate_input_json({"path.vy": "potato"}, language="Vyper")
    with pytest.raises(StructureException):
        compiler.compile_from_input_json(input_json)


def test_build_json_keys(vysource):
    build_json = compiler.compile_and_format({"path.vy": vysource})
    assert set(build.BUILD_KEYS) == set(build_json["path"])


def test_dependencies(vysource):
    code = """
import path as foo
from vyper.interfaces import ERC20
from foo import bar
"""

    build_json = compiler.compile_and_format(
        {"path.vy": vysource, "deps.vy": code, "foo/bar.vy": vysource}
    )
    assert build_json["deps"]["dependencies"] == ["bar", "path"]


def test_compile_empty():
    compiler.compile_and_format({"empty.vy": ""})
