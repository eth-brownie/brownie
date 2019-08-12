#!/usr/bin/python3

from copy import deepcopy

from brownie.project import compiler


def test_expand_build_offsets(testproject):

    source = testproject._project_path.joinpath('contracts/BrownieTester.sol')
    source = {'contracts/BrownieTester.sol': source.open().read()}
    build_json = compiler.compile_and_format(source, '0.5.7')['BrownieTester']
    minified_json = compiler.compile_and_format(source, '0.5.7', minify=True)['BrownieTester']
    expanded_json = testproject._build.expand_build_offsets(deepcopy(minified_json))
    for key in ('coverageMap', 'pcMap'):
        assert expanded_json[key] == build_json[key]
        assert minified_json[key] != build_json[key]
