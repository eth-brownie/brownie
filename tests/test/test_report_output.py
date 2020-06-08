import pytest

from brownie.exceptions import BrownieConfigWarning
from brownie.test import coverage
from brownie.test.output import _build_coverage_output, _build_gas_profile_output


def test_exclude_gas(tester, ext_tester, config):
    tester.useSafeMath(5, 10)
    ext_tester.makeExternalCall(tester, 5)

    report = _build_gas_profile_output()

    config.settings["reports"]["exclude_contracts"] = "ExternalCallTester"
    assert _build_gas_profile_output() != report


def test_exclude_gas_as_list(tester, ext_tester, config):
    tester.useSafeMath(5, 10)
    ext_tester.makeExternalCall(tester, 5)

    report = _build_gas_profile_output()

    config.settings["reports"]["exclude_contracts"] = ["ExternalCallTester"]
    assert _build_gas_profile_output() != report


def test_exclude_gas_internal_calls_no_effect(tester, ext_tester, config):
    tester.useSafeMath(5, 10)
    ext_tester.makeExternalCall(tester, 5)

    report = _build_gas_profile_output()

    config.settings["reports"]["exclude_contracts"] = "SafeMath"
    assert _build_gas_profile_output() == report


def test_exclude_coverage(coverage_mode, tester, config):
    tester.useSafeMath(5, 10)

    coverage_eval = coverage.get_merged_coverage_eval()
    report = _build_coverage_output(coverage_eval)
    assert _build_coverage_output(coverage_eval) == report

    config.settings["reports"]["exclude_contracts"] = "SafeMath"
    assert _build_coverage_output(coverage_eval) != report


def test_exclude_coverage_by_glob(coverage_mode, tester, vypertester, config):
    tester.useSafeMath(5, 10)
    vypertester.overflow(1, 2)

    coverage_eval = coverage.get_merged_coverage_eval()
    report = _build_coverage_output(coverage_eval)
    assert _build_coverage_output(coverage_eval) == report

    config.settings["reports"]["exclude_paths"] = "contracts/*.vy"
    assert _build_coverage_output(coverage_eval) != report


def test_invalid_glob_warns(tester, ext_tester, config):
    tester.useSafeMath(5, 10)
    ext_tester.makeExternalCall(tester, 5)

    config.settings["reports"]["exclude_paths"] = "/contracts"
    with pytest.warns(BrownieConfigWarning):
        _build_gas_profile_output()
