#!/usr/bin/python3

import json
from pathlib import Path
import time

from brownie.cli.utils import color
from brownie.network import history
from . import coverage

COVERAGE_COLORS = [
    (0.5, "bright red"),
    (0.85, "bright yellow"),
    (1, "bright green")
]


def save_coverage_report(coverage_eval, report_path):
    '''Saves a test coverage report for viewing in the GUI.

    Args:
        coverage_eval: Coverage evaluation dict
        report_path: Path to save to. If a folder is given, saves as coverage-ddmmyy

    Returns: Path object where report file was saved'''
    report = {
        'highlights': coverage.get_highlights(coverage_eval),
        'coverage': coverage.get_totals(coverage_eval),
        'sha1': {}  # TODO
    }
    report = json.loads(json.dumps(report, default=sorted))
    report_path = Path(report_path).absolute()
    if report_path.is_dir():
        filename = "coverage-"+time.strftime('%d%m%y')+"{}.json"
        count = len(list(report_path.glob(filename.format('*'))))
        if count:
            last_path = _report_path(report_path, filename, count-1)
            with last_path.open() as fp:
                last_report = json.load(fp)
            if last_report == report:
                print(f"\nCoverage report saved at {last_path}")
                return last_path
        report_path = _report_path(report_path, filename, count)
    with report_path.open('w') as fp:
        json.dump(report, fp, sort_keys=True, indent=2)
    print(f"\nCoverage report saved at {report_path}")
    return report_path


def _report_path(base_path, filename, count):
    return base_path.joinpath(filename.format("-"+str(count) if count else ""))


def print_coverage_totals(coverage_eval):
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


def print_gas_profile():
    '''Formats and prints a gas profile report to the console.'''
    print('\n\nGas Profile:')
    gas = history.gas_profile
    for i in sorted(gas):
        print(f"{i} -  avg: {gas[i]['avg']:.0f}  low: {gas[i]['low']}  high: {gas[i]['high']}")
