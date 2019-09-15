#!/usr/bin/python3


def test_ternery1(evmtester, branch_results):
    evmtester.terneryBranches(1, True, False, False, False)
    results = branch_results()
    assert [2582, 2583] in results[True]
    assert [2610, 2611] in results[False]

    evmtester.terneryBranches(1, False, False, False, False)
    results = branch_results()
    assert [2582, 2583] in results[False]
    assert [2610, 2611] in results[True]


def test_ternery2(evmtester, branch_results):
    evmtester.terneryBranches(2, False, False, False, False)
    results = branch_results()
    for i in [2670, 2704, 2709]:
        assert [i, i + 1] in results[False]

    evmtester.terneryBranches(2, True, False, False, False)
    results = branch_results()
    assert [2675, 2676] in results[False]
    for i in [2670, 2704]:
        assert [i, i + 1] in results[True]

    evmtester.terneryBranches(2, False, True, False, False)
    results = branch_results()
    assert [2709, 2710] in results[True]
    for i in [2670, 2704]:
        assert [i, i + 1] in results[False]

    evmtester.terneryBranches(2, True, True, False, False)
    results = branch_results()
    for i in [2670, 2675, 2704]:
        assert [i, i + 1] in results[True]


def test_ternery3(evmtester, branch_results):
    evmtester.terneryBranches(3, False, False, False, False)
    results = branch_results()
    for i in [2771, 2777, 2807]:
        assert [i, i + 1] in results[True]

    evmtester.terneryBranches(3, True, False, False, False)
    results = branch_results()
    assert [2813, 2814] in results[True]
    for i in [2771, 2807]:
        assert [i, i + 1] in results[False]

    evmtester.terneryBranches(3, False, True, False, False)
    results = branch_results()
    assert [2777, 2778] in results[False]
    for i in [2771, 2807]:
        assert [i, i + 1] in results[True]

    evmtester.terneryBranches(3, True, True, False, False)
    results = branch_results()
    for i in [2771, 2807, 2813]:
        assert [i, i + 1] in results[False]


def test_ternery4(evmtester, branch_results):
    evmtester.terneryBranches(4, False, False, False, False)
    results = branch_results()
    for i in [2874, 2913, 2918, 2923]:
        assert [i, i + 1] in results[False]

    evmtester.terneryBranches(4, True, False, False, False)
    results = branch_results()
    assert [2879, 2880] in results[False]
    for i in [2874, 2913]:
        assert [i, i + 1] in results[True]

    evmtester.terneryBranches(4, False, True, False, False)
    results = branch_results()
    assert [2918, 2919] in results[True]
    for i in [2874, 2913]:
        assert [i, i + 1] in results[False]

    evmtester.terneryBranches(4, False, False, True, False)
    results = branch_results()
    assert [2923, 2924] in results[True]
    for i in [2874, 2913, 2918]:
        assert [i, i + 1] in results[False]

    evmtester.terneryBranches(4, True, True, True, False)
    results = branch_results()
    for i in [2874, 2879, 2884, 2913]:
        assert [i, i + 1] in results[True]


def test_ternery5(evmtester, branch_results):
    evmtester.terneryBranches(5, True, True, True, True)
    results = branch_results()
    for i in [2985, 3027, 3033, 3039]:
        assert [i, i + 1] in results[False]

    evmtester.terneryBranches(5, False, True, True, True)
    results = branch_results()
    assert [2991, 2992] in results[False]
    for i in [2985, 3027]:
        assert [i, i + 1] in results[True]

    evmtester.terneryBranches(5, True, False, True, True)
    results = branch_results()
    assert [3033, 3034] in results[True]
    for i in [2985, 3027]:
        assert [i, i + 1] in results[False]

    evmtester.terneryBranches(5, True, True, False, True)
    results = branch_results()
    assert [3039, 3040] in results[True]
    for i in [2985, 3027, 3033]:
        assert [i, i + 1] in results[False]

    evmtester.terneryBranches(5, False, False, False, False)
    results = branch_results()
    for i in [2985, 2991, 2997, 3027]:
        assert [i, i + 1] in results[True]
