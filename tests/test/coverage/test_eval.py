import copy
import json

import pytest

from brownie.test import coverage, output


def test_merge_transaction_coverage_lists():
    transactions = {
        "first": {"Foo": {"0": [{1}, {2}, set()]}},
        "second": {"Foo": {"0": [{3}, set(), {2}]}},
    }
    before = copy.deepcopy(transactions)
    assert coverage.get_merged_coverage_eval(transactions) == {"Foo": {"0": [{1, 3}, {2}, {2}]}}
    assert transactions == before


@pytest.mark.parametrize("serialized", [False, True])
def test_split_coverage_lists_by_function(serialized):
    coverage_map = {
        "statements": {"0": {"Foo.foo": {1: (0, 5), 3: (6, 10)}}},
        "branches": {"0": {"Foo.foo": {2: (0, 5, True)}}},
    }
    if serialized:
        coverage_map = json.loads(json.dumps(coverage_map))
    expected_ids = ["1"] if serialized else [1]
    expected_branches = ["2"] if serialized else [2]
    assert output._split([{1}, set(), {2}], coverage_map, "0") == {
        "Foo.foo": (expected_ids, [], expected_branches)
    }
    highlights = output._statement_highlights({"0": [{1}, set(), {2}]}, coverage_map["statements"])
    assert highlights["0"] == [[0, 5, "green", ""], [6, 10, "red", ""]]
    assert output._branch_color(2, {"0": [{1}, set(), {2}]}, "0", True) == "yellow"


def test_cached_coverage_report_after_json_roundtrip():
    transactions = {"cached": {"Foo": {"0": [{1}, set(), {2}]}}}
    cached = json.loads(json.dumps(transactions, default=sorted))
    before = copy.deepcopy(cached)
    merged = coverage.get_merged_coverage_eval(cached)
    coverage_map = {
        "statements": {"0": {"Foo.foo": {"1": [0, 5]}}},
        "branches": {"0": {"Foo.foo": {"2": [0, 5, True]}}},
    }
    assert output._split(merged["Foo"]["0"], coverage_map, "0") == {"Foo.foo": (["1"], [], ["2"])}
    assert output._statement_color("1", merged["Foo"], "0") == "green"
    assert output._branch_color(2, merged["Foo"], "0", True) == "yellow"
    assert cached == before
