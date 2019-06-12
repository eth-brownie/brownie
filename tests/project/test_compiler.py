#!/usr/bin/python3

import pytest
import solcx

from brownie.project import compiler, sources, build
from brownie.exceptions import CompilerError


@pytest.fixture(autouse=True, scope="function")
def version():
    yield
    compiler.set_solc_version("v0.5.7")


def _solc_5_source():
    source = sources.get('BrownieTester')
    source = source.replace('BrownieTester', 'TempTester')
    source = source.replace('UnlinkedLib', 'TestLib')
    return source


def _solc_4_source():
    source = _solc_5_source()
    source = source.replace('payable ', '')
    source = source.replace('^0.5.0', '^0.4.25')
    return source


def _solc_4_output_json():
    compiler.set_solc_version("0.4.25")
    source = _solc_4_source()
    input_json = compiler.generate_input_json({'path': source}, True, 200)
    return compiler.compile_from_input_json(input_json)


def _solc_5_output_json():
    source = _solc_5_source()
    input_json = compiler.generate_input_json({'path': source}, True, 200)
    return compiler.compile_from_input_json(input_json)


def test_set_solc_version():
    compiler.set_solc_version("0.5.7")
    assert "0.5.7" in solcx.get_solc_version_string()
    compiler.set_solc_version("0.4.25")
    assert "0.4.25" in solcx.get_solc_version_string()


def test_generate_input_json():
    source = _solc_5_source()
    input_json = compiler.generate_input_json({'path': source}, True, 200)
    assert input_json['settings']['optimizer']['enabled'] is True
    assert input_json['settings']['optimizer']['runs'] == 200
    assert input_json['sources']['path']['content'] == source
    input_json = compiler.generate_input_json({'path': source}, False, 0, True)
    assert input_json['settings']['optimizer']['enabled'] is False
    assert input_json['settings']['optimizer']['runs'] == 0
    assert input_json['sources']['path']['content'] != source


def test_compile_input_json():
    output_json = _solc_5_output_json()
    assert "TempTester" in output_json['contracts']['path']
    assert "TestLib" in output_json['contracts']['path']


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


def test_build_json_keys():
    build_json = compiler.compile_and_format({'path': _solc_5_source()})
    assert set(build.BUILD_KEYS) == set(build_json['TempTester'])


def test_build_json_unlinked_libraries():
    build_json = compiler.compile_and_format({'path': _solc_5_source()})
    assert '__TestLib__' in build_json['TempTester']['bytecode']
    compiler.set_solc_version("v0.4.25")
    build_json = compiler.compile_and_format({'path': _solc_4_source()})
    assert '__TestLib__' in build_json['TempTester']['bytecode']


def test_format_link_references():
    output_json = _solc_5_output_json()
    evm = output_json['contracts']['path']['TempTester']['evm']
    assert '__TestLib__' in compiler.format_link_references(evm)
    output_json = _solc_4_output_json()
    evm = output_json['contracts']['path']['TempTester']['evm']
    assert '__TestLib__' in compiler.format_link_references(evm)


def test_compiler_errors():
    with pytest.raises(CompilerError):
        compiler.compile_and_format({'path': _solc_4_source()})
    solcx.set_solc_version('0.4.25')
    with pytest.raises(CompilerError):
        compiler.compile_and_format({'path': _solc_5_source()})
