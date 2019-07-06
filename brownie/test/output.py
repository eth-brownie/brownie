#!/usr/bin/python3


from brownie.cli.utils import color
from brownie.network import history
from . import coverage

COVERAGE_COLORS = [
    (0.5, "bright red"),
    (0.85, "bright yellow"),
    (1, "bright green")
]


def coverage_totals(coverage_eval):
    '''Formats and prints a coverage evaluation report to the console.

    Args:
        coverage_eval: coverage evaluation dict

    Returns: None'''
    totals = coverage.get_totals(coverage_eval)
    print("\n\nCoverage analysis:")
    for name in sorted(totals):
        pct = _pct(totals[name]['totals']['statements'], totals[name]['totals']['branches'])
        print(f"\n  contract: {color['contract']}{name}{color} - {_cov_color(pct)}{pct:.1%}{color}")
        cov = totals[name]
        for fn_name, count in cov['statements'].items():
            branch = cov['branches'][fn_name] if fn_name in cov['branches'] else (0, 0, 0)
            pct = _pct(count, branch)
            print(f"    {fn_name} - {_cov_color(pct)}{pct:.1%}{color}")


def _cov_color(pct):
    return color(next(i[1] for i in COVERAGE_COLORS if pct <= i[0]))


def _pct(statement, branch):
    pct = statement[0]/statement[1]
    if branch[-1]:
        pct = (pct + (branch[0]+branch[1])/(branch[2]*2)) / 2
    return pct


def gas_profile():
    '''Formats and prints a gas profile report to the console.'''
    print('\n\nGas Profile:')
    gas = history.gas_profile
    for i in sorted(gas):
        print(f"{i} -  avg: {gas[i]['avg']:.0f}  low: {gas[i]['low']}  high: {gas[i]['high']}")
