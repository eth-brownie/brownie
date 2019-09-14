#!/usr/bin/python3


from brownie.test import coverage

PATH = "contracts/EVMTester.sol"


# organizes branch results based on if they evaluated True or False
def _get_branch_results(build):
    branch_false, branch_true = [
        sorted(i)
        for i in list(coverage.get_coverage_eval().values())[0]["EVMTester"][PATH][1:]
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
    cov_map = build["coverageMap"]["branches"][PATH]
    result = next(
        (y for v in cov_map.values() for x, y in v.items() if int(x) == idx), None
    )
    if result:
        return result[-1] == jump, list(result[:-1])
    raise ValueError("Branch map index does not exist")


def test_if1(evmtester, coverage_mode):
    build = evmtester._build

    evmtester.ifBranches(1, True, False, False, False)
    assert [175, 176] in _get_branch_results(build)[True]

    evmtester.ifBranches(1, False, False, False, False)
    results = _get_branch_results(build)
    assert [175, 176] in results[False]
    assert [208, 209] in results[True]


def test_if2(evmtester, coverage_mode):
    build = evmtester._build

    evmtester.ifBranches(2, True, True, False, False)
    results = _get_branch_results(build)
    assert [272, 273] in results[True]
    assert [277, 278] in results[True]

    evmtester.ifBranches(2, False, True, False, False)
    results = _get_branch_results(build)
    assert [272, 273] in results[False]
    assert [309, 310] in results[False]
    assert [314, 315] in results[True]

    evmtester.ifBranches(2, True, False, False, False)
    results = _get_branch_results(build)
    assert [272, 273] in results[True]
    assert [277, 278] in results[False]
    assert [309, 310] in results[True]


def test_if3(evmtester, coverage_mode):
    build = evmtester._build

    evmtester.ifBranches(3, False, False, False, False)
    results = _get_branch_results(build)
    assert [379, 380] in results[True]
    assert [385, 386] in results[True]

    evmtester.ifBranches(3, False, True, False, False)
    results = _get_branch_results(build)
    assert [379, 380] in results[True]
    assert [385, 386] in results[False]
    assert [418, 419] in results[True]

    evmtester.ifBranches(3, True, False, False, False)
    results = _get_branch_results(build)
    assert [379, 380] in results[False]
    assert [418, 419] in results[False]
    assert [424, 425] in results[True]


def test_if4(evmtester, coverage_mode):
    build = evmtester._build

    evmtester.ifBranches(4, True, True, True, False)
    results = _get_branch_results(build)
    assert [488, 489] in results[True]
    assert [493, 494] in results[True]
    assert [498, 499] in results[True]

    evmtester.ifBranches(4, False, True, True, False)
    results = _get_branch_results(build)
    assert [488, 489] in results[False]
    assert [530, 531] in results[False]
    assert [535, 536] in results[True]

    evmtester.ifBranches(4, True, False, True, False)
    results = _get_branch_results(build)
    assert [488, 489] in results[True]
    assert [493, 494] in results[False]
    assert [530, 531] in results[True]

    evmtester.ifBranches(4, True, True, False, False)
    results = _get_branch_results(build)
    assert [488, 489] in results[True]
    assert [493, 494] in results[True]
    assert [498, 499] in results[False]
    assert [530, 531] in results[True]

    evmtester.ifBranches(4, False, False, True, False)
    results = _get_branch_results(build)
    assert [488, 489] in results[False]
    assert [530, 531] in results[False]
    assert [535, 536] in results[False]
    assert [540, 541] in results[True]


def test_if5(evmtester, coverage_mode):
    build = evmtester._build

    evmtester.ifBranches(5, False, False, False, False)
    results = _get_branch_results(build)
    assert [605, 606] in results[True]
    assert [611, 612] in results[True]
    assert [617, 618] in results[True]

    evmtester.ifBranches(5, True, False, False, False)
    results = _get_branch_results(build)
    assert [605, 606] in results[False]
    assert [650, 651] in results[False]
    assert [656, 657] in results[True]

    evmtester.ifBranches(5, False, True, False, False)
    results = _get_branch_results(build)
    assert [605, 606] in results[True]
    assert [611, 612] in results[False]
    assert [650, 651] in results[True]

    evmtester.ifBranches(5, False, False, True, False)
    results = _get_branch_results(build)
    assert [605, 606] in results[True]
    assert [611, 612] in results[True]
    assert [617, 618] in results[False]
    assert [650, 651] in results[True]

    evmtester.ifBranches(5, True, True, False, False)
    results = _get_branch_results(build)
    assert [605, 606] in results[False]
    assert [650, 651] in results[False]
    assert [656, 657] in results[False]
    assert [662, 663] in results[True]


def test_if6(evmtester, coverage_mode):
    build = evmtester._build

    evmtester.ifBranches(6, True, True, True, True)
    results = _get_branch_results(build)
    assert [727, 728] in results[True]
    assert [732, 733] in results[True]

    evmtester.ifBranches(6, False, True, True, True)
    results = _get_branch_results(build)
    assert [727, 728] in results[False]
    assert [739, 740] in results[True]
    assert [744, 745] in results[True]

    evmtester.ifBranches(6, True, False, True, True)
    results = _get_branch_results(build)
    assert [727, 728] in results[True]
    assert [732, 733] in results[False]
    assert [739, 740] in results[True]
    assert [744, 745] in results[True]

    evmtester.ifBranches(6, True, False, True, False)
    results = _get_branch_results(build)
    assert [727, 728] in results[True]
    assert [732, 733] in results[False]
    assert [739, 740] in results[True]
    assert [744, 745] in results[False]
    assert [778, 779] in results[True]
    assert [790, 791] in results[True]

    evmtester.ifBranches(6, False, True, False, True)
    results = _get_branch_results(build)
    assert [727, 728] in results[False]
    assert [739, 740] in results[False]
    assert [778, 779] in results[False]
    assert [783, 784] in results[True]
    assert [790, 791] in results[False]
    assert [795, 796] in results[True]


def test_if7(evmtester, coverage_mode):
    build = evmtester._build

    evmtester.ifBranches(7, False, False, False, False)
    results = _get_branch_results(build)
    assert [862, 863] in results[True]
    assert [868, 869] in results[True]

    evmtester.ifBranches(7, True, False, False, False)
    results = _get_branch_results(build)
    assert [862, 863] in results[False]
    assert [876, 877] in results[True]
    assert [882, 883] in results[True]

    evmtester.ifBranches(7, False, True, False, False)
    results = _get_branch_results(build)
    assert [862, 863] in results[True]
    assert [868, 869] in results[False]
    assert [876, 877] in results[True]
    assert [882, 883] in results[True]

    evmtester.ifBranches(7, False, True, False, True)
    results = _get_branch_results(build)
    assert [862, 863] in results[True]
    assert [868, 869] in results[False]
    assert [876, 877] in results[True]
    assert [882, 883] in results[False]
    assert [917, 918] in results[True]
    assert [931, 932] in results[True]

    evmtester.ifBranches(7, True, False, True, False)
    results = _get_branch_results(build)
    assert [862, 863] in results[False]
    assert [876, 877] in results[False]
    assert [917, 918] in results[False]
    assert [923, 924] in results[True]
    assert [931, 932] in results[False]
    assert [937, 938] in results[True]
