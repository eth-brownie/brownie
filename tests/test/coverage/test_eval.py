import copy

from brownie.test import coverage, output


def test_merge_transaction_coverage_lists():
    transactions = {
        "first": {"Foo": {"0": [{1}, {2}, set()]}},
        "second": {"Foo": {"0": [{3}, set(), {2}]}},
    }
    before = copy.deepcopy(transactions)
    assert coverage.get_merged_coverage_eval(transactions) == {"Foo": {"0": [{1, 3}, {2}, {2}]}}
    assert transactions == before


def test_split_coverage_lists_by_function():
    coverage_map = {
        "statements": {"0": {"Foo.foo": {1: (0, 5), 3: (6, 10)}}},
        "branches": {"0": {"Foo.foo": {2: (0, 5, True)}}},
    }
    assert output._split([{1}, set(), {2}], coverage_map, "0") == {"Foo.foo": ([1], [], [2])}
    assert output._branch_color(2, {"0": [{1}, set(), {2}]}, "0", True) == "yellow"
