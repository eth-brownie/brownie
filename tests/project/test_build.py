#!/usr/bin/python3

from copy import deepcopy

from brownie.project.compiler import compile_and_format


def test_expand_build_offsets(testproject, btsource):
    source = {"contracts/BrownieTester.sol": btsource}
    build_json = compile_and_format(source, "0.5.7", allow_paths=".")["BrownieTester"]
    minified = compile_and_format(source, "0.5.7", minify=True, allow_paths=".")["BrownieTester"]
    expanded_json = testproject._build.expand_build_offsets(deepcopy(minified))
    for key in ("coverageMap", "pcMap"):
        assert expanded_json[key] == build_json[key]
        assert minified[key] != build_json[key]
