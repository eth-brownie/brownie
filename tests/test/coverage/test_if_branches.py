#!/usr/bin/python3


def test_if1(evmtester, branch_results):
    evmtester.ifBranches(1, True, False, False, False)
    assert [175, 176] in branch_results()[True]

    evmtester.ifBranches(1, False, False, False, False)
    results = branch_results()
    assert [175, 176] in results[False]
    assert [208, 209] in results[True]


def test_if2(evmtester, branch_results):
    evmtester.ifBranches(2, True, True, False, False)
    results = branch_results()
    assert [272, 273] in results[True]
    assert [277, 278] in results[True]

    evmtester.ifBranches(2, False, True, False, False)
    results = branch_results()
    assert [272, 273] in results[False]
    assert [309, 310] in results[False]
    assert [314, 315] in results[True]

    evmtester.ifBranches(2, True, False, False, False)
    results = branch_results()
    assert [272, 273] in results[True]
    assert [277, 278] in results[False]
    assert [309, 310] in results[True]


def test_if3(evmtester, branch_results):
    evmtester.ifBranches(3, False, False, False, False)
    results = branch_results()
    assert [379, 380] in results[True]
    assert [385, 386] in results[True]

    evmtester.ifBranches(3, False, True, False, False)
    results = branch_results()
    assert [379, 380] in results[True]
    assert [385, 386] in results[False]
    assert [418, 419] in results[True]

    evmtester.ifBranches(3, True, False, False, False)
    results = branch_results()
    assert [379, 380] in results[False]
    assert [418, 419] in results[False]
    assert [424, 425] in results[True]


def test_if4(evmtester, branch_results):
    evmtester.ifBranches(4, True, True, True, False)
    results = branch_results()
    assert [488, 489] in results[True]
    assert [493, 494] in results[True]
    assert [498, 499] in results[True]

    evmtester.ifBranches(4, False, True, True, False)
    results = branch_results()
    assert [488, 489] in results[False]
    assert [530, 531] in results[False]
    assert [535, 536] in results[True]

    evmtester.ifBranches(4, True, False, True, False)
    results = branch_results()
    assert [488, 489] in results[True]
    assert [493, 494] in results[False]
    assert [530, 531] in results[True]

    evmtester.ifBranches(4, True, True, False, False)
    results = branch_results()
    assert [488, 489] in results[True]
    assert [493, 494] in results[True]
    assert [498, 499] in results[False]
    assert [530, 531] in results[True]

    evmtester.ifBranches(4, False, False, True, False)
    results = branch_results()
    assert [488, 489] in results[False]
    assert [530, 531] in results[False]
    assert [535, 536] in results[False]
    assert [540, 541] in results[True]


def test_if5(evmtester, branch_results):
    evmtester.ifBranches(5, False, False, False, False)
    results = branch_results()
    assert [605, 606] in results[True]
    assert [611, 612] in results[True]
    assert [617, 618] in results[True]

    evmtester.ifBranches(5, True, False, False, False)
    results = branch_results()
    assert [605, 606] in results[False]
    assert [650, 651] in results[False]
    assert [656, 657] in results[True]

    evmtester.ifBranches(5, False, True, False, False)
    results = branch_results()
    assert [605, 606] in results[True]
    assert [611, 612] in results[False]
    assert [650, 651] in results[True]

    evmtester.ifBranches(5, False, False, True, False)
    results = branch_results()
    assert [605, 606] in results[True]
    assert [611, 612] in results[True]
    assert [617, 618] in results[False]
    assert [650, 651] in results[True]

    evmtester.ifBranches(5, True, True, False, False)
    results = branch_results()
    assert [605, 606] in results[False]
    assert [650, 651] in results[False]
    assert [656, 657] in results[False]
    assert [662, 663] in results[True]


def test_if6(evmtester, branch_results):
    evmtester.ifBranches(6, True, True, True, True)
    results = branch_results()
    assert [727, 728] in results[True]
    assert [732, 733] in results[True]

    evmtester.ifBranches(6, False, True, True, True)
    results = branch_results()
    assert [727, 728] in results[False]
    assert [739, 740] in results[True]
    assert [744, 745] in results[True]

    evmtester.ifBranches(6, True, False, True, True)
    results = branch_results()
    assert [727, 728] in results[True]
    assert [732, 733] in results[False]
    assert [739, 740] in results[True]
    assert [744, 745] in results[True]

    evmtester.ifBranches(6, True, False, True, False)
    results = branch_results()
    assert [727, 728] in results[True]
    assert [732, 733] in results[False]
    assert [739, 740] in results[True]
    assert [744, 745] in results[False]
    assert [778, 779] in results[True]
    assert [790, 791] in results[True]

    evmtester.ifBranches(6, False, True, False, True)
    results = branch_results()
    assert [727, 728] in results[False]
    assert [739, 740] in results[False]
    assert [778, 779] in results[False]
    assert [783, 784] in results[True]
    assert [790, 791] in results[False]
    assert [795, 796] in results[True]


def test_if7(evmtester, branch_results):
    evmtester.ifBranches(7, False, False, False, False)
    results = branch_results()
    assert [862, 863] in results[True]
    assert [868, 869] in results[True]

    evmtester.ifBranches(7, True, False, False, False)
    results = branch_results()
    assert [862, 863] in results[False]
    assert [876, 877] in results[True]
    assert [882, 883] in results[True]

    evmtester.ifBranches(7, False, True, False, False)
    results = branch_results()
    assert [862, 863] in results[True]
    assert [868, 869] in results[False]
    assert [876, 877] in results[True]
    assert [882, 883] in results[True]

    evmtester.ifBranches(7, False, True, False, True)
    results = branch_results()
    assert [862, 863] in results[True]
    assert [868, 869] in results[False]
    assert [876, 877] in results[True]
    assert [882, 883] in results[False]
    assert [917, 918] in results[True]
    assert [931, 932] in results[True]

    evmtester.ifBranches(7, True, False, True, False)
    results = branch_results()
    assert [862, 863] in results[False]
    assert [876, 877] in results[False]
    assert [917, 918] in results[False]
    assert [923, 924] in results[True]
    assert [931, 932] in results[False]
    assert [937, 938] in results[True]
