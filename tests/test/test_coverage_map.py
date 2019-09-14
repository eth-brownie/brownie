#!/usr/bin/python3

import pytest

from brownie.test import coverage
from brownie.exceptions import VirtualMachineError

PATH = "contracts/EVMTester.sol"


def _get_map(build, idx):
    for key in ("statements", "branches"):
        cov_map = build["coverageMap"][key][PATH]
        result = next(
            (y for v in cov_map.values() for x, y in v.items() if int(x) == idx), None
        )
        if result:
            return result
    raise ValueError("Coverage map index does not exist")


def _get_cov():
    return [
        sorted(i)
        for i in list(coverage.get_coverage_eval().values())[0]["EVMTester"][PATH]
    ]


def test_coverage_if(evmtester, coverage_mode):
    build = evmtester._build
    evmtester.ifBranches(True, False, True, False)
    stmt, branch_true, branch_false = _get_cov()
    assert _get_map(build, stmt[0]) == (289, 293)
    branch_iter = iter(
        [
            (141, 142, False),
            (185, 186, False),
            (190, 191, True),
            (197, 198, False),
            (267, 268, False),
        ]
    )
    for idx in branch_true:
        assert _get_map(build, idx) == next(branch_iter)
    branch_iter = iter(
        [(146, 147, False), (202, 203, False), (231, 232, True), (273, 274, True)]
    )
    for idx in branch_false:
        assert _get_map(build, idx) == next(branch_iter)


def test_coverage_require(evmtester, coverage_mode):
    build = evmtester._build
    with pytest.raises(VirtualMachineError):
        evmtester.requireBranches(False, True, True, False)
    stmt, branch_true, branch_false = _get_cov()
    stmt_iter = iter([(469, 494), (504, 533), (543, 565)])
    for idx in stmt:
        assert _get_map(build, idx) == next(stmt_iter)
    branch_iter = iter(
        [(477, 478, True), (513, 514, True), (518, 519, False), (563, 564, True)]
    )
    for idx in branch_true:
        assert _get_map(build, idx) == next(branch_iter)
    branch_iter = iter([(482, 483, True), (525, 526, True), (552, 553, False)])
    for idx in branch_false:
        assert _get_map(build, idx) == next(branch_iter)


def test_coverage_ternery(evmtester, coverage_mode):
    build = evmtester._build
    evmtester.terneryBranches(False, True)
    stmt, branch_true, branch_false = _get_cov()
    stmt_iter = iter([(672, 692), (702, 727), (737, 762), (779, 783)])
    for idx in stmt:
        assert _get_map(build, idx) == next(stmt_iter)
    branch_iter = iter([(682, 683, False), (747, 748, True)])
    for idx in branch_true:
        assert _get_map(build, idx) == next(branch_iter)
    branch_iter = iter([(712, 713, False), (752, 753, False)])
    for idx in branch_false:
        assert _get_map(build, idx) == next(branch_iter)
