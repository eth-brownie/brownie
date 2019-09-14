#!/usr/bin/python3

from pathlib import Path
import json
import pytest

conf_source = """
import pytest

@pytest.fixture(autouse=True)
def isolation(module_isolation):
    pass"""

test_source = """
def test_stuff(BrownieTester, accounts):
    c = accounts[0].deploy(BrownieTester, True)
    c.doNothing({'from': accounts[0]})"""


@pytest.fixture
def runconf(plugintester):
    plugintester.makeconftest(conf_source)
    result = plugintester.runpytest("-U")
    result.assert_outcomes(passed=1)


def test_update_no_isolation(plugintester):
    result = plugintester.runpytest()
    result.assert_outcomes(passed=1)
    result = plugintester.runpytest("-U")
    result.assert_outcomes(passed=1)


def test_update_isolation(runconf, plugintester):
    result = plugintester.runpytest("-U")
    result.assert_outcomes(skipped=1)


def test_update_isolation_coverage(runconf, plugintester):
    result = plugintester.runpytest("-C", "-U")
    result.assert_outcomes(passed=1)
    result = plugintester.runpytest("-C", "-U")
    result.assert_outcomes(skipped=1)
    result = plugintester.runpytest("-U")
    result.assert_outcomes(skipped=1)
    plugintester.runpytest()
    result = plugintester.runpytest("-C", "-U")
    result.assert_outcomes(skipped=1)


def test_update_isolation_contract_changed(runconf, json_path, plugintester):
    with Path(plugintester.tmpdir).joinpath("contracts/BrownieTester.sol").open(
        "a"
    ) as fp:
        fp.write("\n\ncontract Foo {}")
    result = plugintester.runpytest("-U")
    result.assert_outcomes(passed=1)


def test_update_isolation_testfile_changed(runconf, json_path, plugintester):
    with json_path.open() as fp:
        build = json.load(fp)
    build["tests"]["test_update_isolation_testfile_changed.py"]["sha1"] = "potato"
    with json_path.open("w") as fp:
        build = json.dump(build, fp)

    result = plugintester.runpytest("-U")
    result.assert_outcomes(passed=1)
