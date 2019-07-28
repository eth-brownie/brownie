#!/usr/bin/python3

import pytest
import solcx

from brownie.project import compiler, build
from brownie.exceptions import CompilerError, IncompatibleSolcVersion


@pytest.fixture(scope="module")
def solc4json(solc4source):
    compiler.set_solc_version("0.4.25")
    input_json = compiler.generate_input_json({'path': solc4source}, True, 200)
    yield compiler.compile_from_input_json(input_json)


@pytest.fixture(scope="module")
def solc5json(solc5source):
    compiler.set_solc_version("0.5.7")
    input_json = compiler.generate_input_json({'path': solc5source}, True, 200)
    yield compiler.compile_from_input_json(input_json)


def test_set_solc_version():
    compiler.set_solc_version("0.5.7")
    assert "0.5.7" in solcx.get_solc_version_string()
    compiler.set_solc_version("0.4.25")
    assert "0.4.25" in solcx.get_solc_version_string()


def test_generate_input_json(solc5source):
    input_json = compiler.generate_input_json({'path': solc5source}, True, 200)
    assert input_json['settings']['optimizer']['enabled'] is True
    assert input_json['settings']['optimizer']['runs'] == 200
    assert input_json['sources']['path']['content'] == solc5source
    input_json = compiler.generate_input_json({'path': solc5source}, False, 0, minify=True)
    assert input_json['settings']['optimizer']['enabled'] is False
    assert input_json['settings']['optimizer']['runs'] == 0
    assert input_json['sources']['path']['content'] != solc5source


def test_compile_input_json(solc5json):
    assert "TempTester" in solc5json['contracts']['path']
    assert "TestLib" in solc5json['contracts']['path']


def test_compile_input_json_raises():
    input_json = compiler.generate_input_json({'path': "potato"}, True, 200)
    with pytest.raises(CompilerError):
        compiler.compile_from_input_json(input_json)


def test_compile_optimizer(monkeypatch):
    def _test_compiler(a, **kwargs):
        assert kwargs['optimize'] is True
        assert kwargs['optimize_runs'] == 666
    monkeypatch.setattr('solcx.compile_standard', _test_compiler)
    input_json = {'settings': {'optimizer': {'enabled': True, 'runs': 666}}}
    compiler.compile_from_input_json(input_json)
    input_json = {'settings': {'optimizer': {'enabled': True, 'runs': 31337}}}
    with pytest.raises(AssertionError):
        compiler.compile_from_input_json(input_json)
    input_json = {'settings': {'optimizer': {'enabled': False, 'runs': 666}}}
    with pytest.raises(AssertionError):
        compiler.compile_from_input_json(input_json)


def test_build_json_keys(solc5source):
    build_json = compiler.compile_and_format({'path': solc5source})
    assert set(build.BUILD_KEYS) == set(build_json['TempTester'])


def test_build_json_unlinked_libraries(solc4source, solc5source):
    build_json = compiler.compile_and_format({'path': solc5source}, solc_version="0.5.7")
    assert '__TestLib__' in build_json['TempTester']['bytecode']
    build_json = compiler.compile_and_format({'path': solc4source}, solc_version="0.4.25")
    assert '__TestLib__' in build_json['TempTester']['bytecode']


def test_format_link_references(solc4json, solc5json):
    evm = solc5json['contracts']['path']['TempTester']['evm']
    assert '__TestLib__' in compiler.format_link_references(evm)
    evm = solc4json['contracts']['path']['TempTester']['evm']
    assert '__TestLib__' in compiler.format_link_references(evm)


def test_compiler_errors(solc4source, solc5source):
    with pytest.raises(CompilerError):
        compiler.compile_and_format({'path': solc4source}, solc_version="0.5.7")
    with pytest.raises(CompilerError):
        compiler.compile_and_format({'path': solc5source}, solc_version="0.4.25")


def test_min_version():
    with pytest.raises(IncompatibleSolcVersion):
        compiler.set_solc_version('v0.4.21')
