#!/usr/bin/python3

import functools

import pytest

from brownie.test import coverage


@pytest.fixture
def branch_results(coverage_mode, evmtester):
    build = evmtester._build
    yield functools.partial(_get_branch_results, build)


# organizes branch results based on if they evaluated True or False
def _get_branch_results(build):
    branch_false, branch_true = [
        sorted(i) for i in list(coverage.get_coverage_eval().values())[0]["EVMTester"]["0"][1:]
    ]
    coverage.clear()
    branch_results = {True: [], False: []}
    for i in branch_true:
        key, map_ = _get_branch(build, i, True)
        branch_results[key].append(map_)
    for i in branch_false:
        key, map_ = _get_branch(build, i, False)
        branch_results[key].append(map_)
    return branch_results


def _get_branch(build, idx, jump):
    cov_map = build["coverageMap"]["branches"]["0"]
    result = next((y for v in cov_map.values() for x, y in v.items() if int(x) == idx), None)
    if result:
        return result[-1] == jump, list(result[:-1])
    raise ValueError("Branch map index does not exist")
