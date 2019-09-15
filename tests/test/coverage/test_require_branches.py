#!/usr/bin/python3

import pytest

from brownie.exceptions import VirtualMachineError


def test_require1(evmtester, branch_results):
    evmtester.requireBranches(1, True, False, False, False)
    results = branch_results()
    assert [1106, 1107] in results[True]
    assert [1130, 1131] in results[True]

    with pytest.raises(VirtualMachineError):
        evmtester.requireBranches(1, False, False, False, False)
    results = branch_results()
    assert [1106, 1107] in results[False]


def test_require2(evmtester, branch_results):
    evmtester.requireBranches(2, False, False, False, False)
    results = branch_results()
    assert [1195, 1197] in results[True]
    assert [1220, 1222] in results[True]

    with pytest.raises(VirtualMachineError):
        evmtester.requireBranches(2, True, False, False, False)
    results = branch_results()
    assert [1195, 1197] in results[False]


def test_require3(evmtester, branch_results):
    evmtester.requireBranches(3, True, True, False, False)
    results = branch_results()
    for i in [1286, 1315, 1353, 1358, 1382, 1387]:
        assert [i, i + 1] in results[True]

    with pytest.raises(VirtualMachineError):
        evmtester.requireBranches(3, True, False, False, False)
    results = branch_results()
    for i in [1286, 1315, 1353]:
        assert [i, i + 1] in results[True]
    assert [1358, 1359] in results[False]

    with pytest.raises(VirtualMachineError):
        evmtester.requireBranches(3, False, True, False, False)
    results = branch_results()
    for i in [1291, 1320]:
        assert [i, i + 1] in results[True]
    for i in [1286, 1315, 1353]:
        assert [i, i + 1] in results[False]


def test_require4(evmtester, branch_results):
    evmtester.requireBranches(4, False, False, False, False)
    results = branch_results()
    for i in [1453, 1484, 1524, 1530, 1555, 1561]:
        assert [i, i + 1] in results[True]

    with pytest.raises(VirtualMachineError):
        evmtester.requireBranches(4, False, True, False, False)
    results = branch_results()
    for i in [1453, 1484, 1524]:
        assert [i, i + 1] in results[True]
    assert [1530, 1531] in results[False]

    with pytest.raises(VirtualMachineError):
        evmtester.requireBranches(4, True, False, False, False)
    results = branch_results()
    for i in [1459, 1490]:
        assert [i, i + 1] in results[True]
    for i in [1453, 1484, 1524]:
        assert [i, i + 1] in results[False]


def test_require5(evmtester, branch_results):
    evmtester.requireBranches(5, True, True, True, False)
    results = branch_results()
    for i in [1626, 1660, 1703, 1708, 1713, 1737, 1742, 1747]:
        assert [i, i + 1] in results[True]

    with pytest.raises(VirtualMachineError):
        evmtester.requireBranches(5, False, True, True, False)
    results = branch_results()
    for i in [1631, 1665]:
        assert [i, i + 1] in results[True]
    for i in [1626, 1660, 1703]:
        assert [i, i + 1] in results[False]

    with pytest.raises(VirtualMachineError):
        evmtester.requireBranches(5, True, False, True, False)
    results = branch_results()
    for i in [1626, 1660, 1703]:
        assert [i, i + 1] in results[True]
    assert [1708, 1709] in results[False]

    with pytest.raises(VirtualMachineError):
        evmtester.requireBranches(5, True, True, False, False)
    results = branch_results()
    for i in [1626, 1660, 1703, 1708]:
        assert [i, i + 1] in results[True]
    assert [1713, 1714] in results[False]


def test_require6(evmtester, branch_results):
    evmtester.requireBranches(6, False, False, False, False)
    results = branch_results()
    for i in [1813, 1850, 1896, 1902, 1908, 1933, 1939, 1945]:
        assert [i, i + 1] in results[True]

    with pytest.raises(VirtualMachineError):
        evmtester.requireBranches(6, True, False, False, False)
    results = branch_results()
    for i in [1819, 1856]:
        assert [i, i + 1] in results[True]
    for i in [1813, 1850, 1896]:
        assert [i, i + 1] in results[False]

    with pytest.raises(VirtualMachineError):
        evmtester.requireBranches(6, False, True, False, False)
    results = branch_results()
    for i in [1813, 1850, 1896]:
        assert [i, i + 1] in results[True]
    assert [1902, 1903] in results[False]

    with pytest.raises(VirtualMachineError):
        evmtester.requireBranches(6, False, False, True, False)
    results = branch_results()
    for i in [1813, 1850, 1896, 1902]:
        assert [i, i + 1] in results[True]
    assert [1908, 1909] in results[False]


def test_require7(evmtester, branch_results):
    evmtester.requireBranches(7, True, True, True, True)
    results = branch_results()
    for i in [2011, 2016, 2054, 2059, 2106, 2118, 2149, 2161]:
        assert [i, i + 1] in results[True]

    evmtester.requireBranches(7, False, True, True, True)
    results = branch_results()
    for i in [2023, 2028, 2066, 2071, 2111, 2118, 2154, 2161]:
        assert [i, i + 1] in results[True]
    for i in [2011, 2054, 2106, 2149]:
        assert [i, i + 1] in results[False]

    evmtester.requireBranches(7, True, False, True, True)
    results = branch_results()
    for i in [2011, 2023, 2028, 2054, 2066, 2071, 2106, 2118, 2149, 2161]:
        assert [i, i + 1] in results[True]
    for i in [2016, 2059]:
        assert [i, i + 1] in results[False]

    evmtester.requireBranches(7, True, True, False, True)
    results = branch_results()
    for i in [2011, 2016, 2054, 2059, 2106, 2123, 2149, 2166]:
        assert [i, i + 1] in results[True]
    for i in [2118, 2161]:
        assert [i, i + 1] in results[False]


def test_require8(evmtester, branch_results):
    evmtester.requireBranches(8, False, False, False, False)
    results = branch_results()
    for i in [2234, 2240, 2281, 2287, 2337, 2351, 2384, 2398]:
        assert [i, i + 1] in results[True]

    evmtester.requireBranches(8, True, False, False, False)
    results = branch_results()
    for i in [2248, 2254, 2295, 2301, 2343, 2351, 2390, 2398]:
        assert [i, i + 1] in results[True]
    for i in [2234, 2281, 2337, 2384]:
        assert [i, i + 1] in results[False]

    evmtester.requireBranches(8, False, True, False, False)
    results = branch_results()
    for i in [2234, 2254, 2295, 2281, 2295, 2301, 2337, 2351, 2384, 2398]:
        assert [i, i + 1] in results[True]
    for i in [2240, 2287]:
        assert [i, i + 1] in results[False]

    evmtester.requireBranches(8, False, False, True, False)
    results = branch_results()
    for i in [2234, 2240, 2281, 2287, 2337, 2357, 2384, 2404]:
        assert [i, i + 1] in results[True]
    for i in [2351, 2398]:
        assert [i, i + 1] in results[False]
