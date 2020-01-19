#!/usr/bin/python3

import json
from pathlib import Path

import pytest

test_source = """
def test_stuff(BrownieTester, accounts):
    c = accounts[0].deploy(BrownieTester, True)
    c.doNothing({'from': accounts[0]})"""


def test_update_no_isolation(plugintester):
    result = plugintester.runpytest()
    result.assert_outcomes(passed=1)
    result = plugintester.runpytest("-U")
    result.assert_outcomes(passed=1)


@pytest.mark.parametrize("arg", ["", "-n 2"])
def test_update_isolation(isolatedtester, arg):
    result = isolatedtester.runpytest(arg)
    result.assert_outcomes(passed=1)
    result = isolatedtester.runpytest("-U", arg)
    result.assert_outcomes(skipped=1)


@pytest.mark.parametrize("arg", ["", "-n 2"])
def test_update_isolation_coverage(isolatedtester, arg):
    result = isolatedtester.runpytest("-U", arg)
    result.assert_outcomes(passed=1)
    result = isolatedtester.runpytest("-C", "-U", arg)
    result.assert_outcomes(passed=1)
    result = isolatedtester.runpytest("-C", "-U", arg)
    result.assert_outcomes(skipped=1)
    result = isolatedtester.runpytest("-U", arg)
    result.assert_outcomes(skipped=1)
    isolatedtester.runpytest(arg)
    result = isolatedtester.runpytest("-C", "-U", arg)
    result.assert_outcomes(skipped=1)


@pytest.mark.parametrize("arg", ["", "-n 2"])
def test_update_isolation_contract_changed(isolatedtester, arg):
    isolatedtester.runpytest()

    path = Path(isolatedtester.tmpdir).joinpath("contracts/BrownieTester.sol")
    with path.open() as fp:
        source = fp.read()
    source = source.replace("two", "tree fiddy")
    with path.open("w") as fp:
        fp.write(source)
    result = isolatedtester.runpytest("-U", arg)
    result.assert_outcomes(passed=1)


@pytest.mark.parametrize("arg", ["", "-n 2"])
def test_update_isolation_testfile_changed(json_path, isolatedtester, arg):
    isolatedtester.runpytest()

    with json_path.open() as fp:
        build = json.load(fp)
    build["tests"]["tests/test_0.py"]["sha1"] = "potato"
    with json_path.open("w") as fp:
        build = json.dump(build, fp)

    result = isolatedtester.runpytest("-U", arg)
    result.assert_outcomes(passed=1)
