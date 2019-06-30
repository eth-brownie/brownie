#!/usr/bin/python3

from copy import deepcopy

from brownie.project import build, compiler, sources


def test_expand_build_offsets():
    source = sources.get("BrownieTester")
    build_json = compiler.compile_and_format({'path': source})['BrownieTester']
    minified_json = compiler.compile_and_format({'path': source}, minify=True)['BrownieTester']
    expanded_json = build.expand_build_offsets(deepcopy(minified_json))
    for key in ('coverageMap', 'pcMap'):
        assert expanded_json[key] == build_json[key]
        assert minified_json[key] != build_json[key]
