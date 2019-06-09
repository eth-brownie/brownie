#!/usr/bin/python3

import pytest

from brownie import project
from brownie.test import coverage
from brownie.network import accounts, history

# untested methods: get_highlights


coverage_map = {
    'branches': {
        'contracts/CoverageTester.sol': {
            'CoverageTester.ifBranches': {
                '28': [144, 145, False],
                '29': [149, 150, False],
                '30': [154, 155, False],
                '31': [159, 160, False],
                '32': [188, 189, False],
                '33': [193, 194, True],
                '34': [200, 201, False],
                '35': [205, 206, False],
                '36': [234, 235, True],
                '37': [239, 240, True],
                '38': [244, 245, True],
                '39': [249, 250, False],
                '40': [270, 271, False],
                '41': [276, 277, True],
                '42': [281, 282, False]
            },
            'CoverageTester.requireBranches': {
                '12': [480, 481, True],
                '13': [485, 486, True],
                '14': [490, 491, True],
                '15': [495, 496, True],
                '16': [516, 517, True],
                '17': [521, 522, False],
                '18': [528, 529, True],
                '19': [533, 534, True],
                '20': [555, 556, False],
                '21': [560, 561, True],
                '22': [566, 567, True]
            },
            'CoverageTester.terneryBranches': {
                '23': [685, 686, False],
                '24': [715, 716, False],
                '25': [720, 721, False],
                '26': [750, 751, True],
                '27': [755, 756, False]
            }
        }
    },
    'statements': {
        'contracts/CoverageTester.sol': {
            'CoverageTester.ifBranches': {
                '10': [292, 296],
                '11': [334, 339],
                '8': [169, 173],
                '9': [216, 220]
            },
            'CoverageTester.requireBranches': {
                '0': [472, 497],
                '1': [507, 536],
                '2': [546, 568],
                '3': [585, 589]
            },
            'CoverageTester.terneryBranches': {
                '4': [675, 695],
                '5': [705, 730],
                '6': [740, 765],
                '7': [782, 786]
            }
        }
    }
}


@pytest.fixture(autouse=True, scope="module")
def covtest():
    project.compiler.set_solc_version('v0.5.0')
    project.close()
    project.load('tests/brownie-test-project')
    c = project.CoverageTester.deploy({'from': accounts[0]})
    c.requireBranches(True, False, True, False)
    c.terneryBranches(True, False)
    yield c


def test_coverage_map(covtest):
    assert covtest._build['coverageMap'] == coverage_map


def test_analyze_statements():
    assert _nested(coverage.analyze(history[-2:-1]), "statements") == {0, 1, 2, 3}
    assert _nested(coverage.analyze(history[-1:]), "statements") == {4, 5, 6, 7}


def test_analyze_branches(covtest):
    cov = coverage.analyze(history[-2:])['CoverageTester']['branches']
    assert 12 in cov['true']['contracts/CoverageTester.sol']
    assert 12 not in cov['false']['contracts/CoverageTester.sol']
    assert 25 not in cov['true']['contracts/CoverageTester.sol']
    assert 25 in cov['false']['contracts/CoverageTester.sol']


def _nested(coverage_eval, key):
    return coverage_eval['CoverageTester'][key]['contracts/CoverageTester.sol']


def test_merge():
    cov1 = coverage.analyze(history[-2:-1])
    cov2 = coverage.analyze(history[-1:])
    merged = coverage.merge([cov1, cov2])
    assert merged != cov1 != cov2
    assert merged == coverage.analyze(history[-2:])


def test_split_by_fn():
    cov = coverage.analyze(history[-2:])
    fn = _nested(coverage.split_by_fn(cov), 'statements')
    assert fn['CoverageTester.requireBranches'] == ["0", "1", "2", "3"]
    assert fn['CoverageTester.terneryBranches'] == ["4", "5", "6", "7"]


def test_get_totals_statements():
    cov = coverage.analyze(history[-2:])
    totals = coverage.get_totals(cov)['CoverageTester']['statements']
    assert totals['CoverageTester.requireBranches'] == (4, 4)
    assert totals['CoverageTester.ifBranches'] == (0, 4)


def test_get_totals_branches():
    cov = coverage.analyze(history[-2:])
    totals = coverage.get_totals(cov)['CoverageTester']['branches']
    assert totals['CoverageTester.terneryBranches'] == (2, 2, 5)
    assert totals['CoverageTester.ifBranches'] == (0, 0, 15)
