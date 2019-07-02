#!/usr/bin/python3

import sys
import time


from brownie.cli.utils import color
from brownie.network import history
from . import coverage

COVERAGE_COLORS = [
    (0.5, "bright red"),
    (0.85, "bright yellow"),
    (1, "bright green")
]


class TestPrinter:

    grand_count = 1
    grand_total = 0

    def __init__(self, path, count, total):
        self.path = path
        self.count = count
        self.total = total
        self.total_time = time.time()
        print(
            f"\nRunning {color['module']}{path}{color} - {self.total} test"
            f"{'s' if total != 1 else ''} ({self.grand_count}/{self.grand_total})"
        )

    @classmethod
    def set_grand_total(cls, total):
        cls.grand_total = total

    def skip(self, description):
        self._print(
            f"{description} ({color['pending']}skipped{color['dull']})\n",
            "\u229d",
            "pending",
            "dull"
        )
        self.count += 1

    def start(self, description):
        self.desc = description
        self._print(f"{description} ({self.count}/{self.total})...")
        self.time = time.time()

    def stop(self, err=None, expect=False):
        if not err:
            self._print(f"{self.desc} ({time.time() - self.time:.4f}s)  \n", "\u2713")
        else:
            err = type(err).__name__
            color_str = 'success' if expect and err != "ExpectedFailing" else 'error'
            symbol = '\u2717' if err in ("AssertionError", "VirtualMachineError") else '\u203C'
            msg = f"{self.desc} ({color(color_str)}{err}{color['dull']})\n"
            self._print(msg, symbol, color_str, "dull")
        self.count += 1

    def finish(self):
        print(
            f"Completed {color['module']}{self.path}{color} ({time.time() - self.total_time:.4f}s)"
        )
        TestPrinter.grand_count += 1

    def _print(self, msg, symbol=" ", symbol_color="success", main_color=None):
        sys.stdout.write(
            f"\r {color[symbol_color]}{symbol}{color[main_color]} {self.count} - {msg}{color}"
        )
        sys.stdout.flush()


def coverage_totals(coverage_eval):
    '''Formats and prints a coverage evaluation report to the console.

    Args:
        coverage_eval: coverage evaluation dict

    Returns: None'''
    totals = coverage.get_totals(coverage_eval)
    print("\nCoverage analysis:")
    for name in sorted(totals):
        pct = _pct(totals[name]['totals']['statements'], totals[name]['totals']['branches'])
        print(f"\n  contract: {color['contract']}{name}{color} - {_cov_color(pct)}{pct:.1%}{color}")
        cov = totals[name]
        for fn_name, count in cov['statements'].items():
            branch = cov['branches'][fn_name] if fn_name in cov['branches'] else (0, 0, 0)
            pct = _pct(count, branch)
            print(
                f"    {color['contract_method']}{fn_name}{color}"
                f" - {_cov_color(pct)}{pct:.1%}{color}"
            )


def _cov_color(pct):
    return color(next(i[1] for i in COVERAGE_COLORS if pct <= i[0]))


def _pct(statement, branch):
    pct = statement[0]/statement[1]
    if branch[-1]:
        pct = (pct + (branch[0]+branch[1])/(branch[2]*2)) / 2
    return pct


def gas_profile():
    '''Formats and prints a gas profile report to the console.'''
    print('\nGas Profile:')
    gas = history.gas_profile
    for i in sorted(gas):
        print(f"{i} -  avg: {gas[i]['avg']:.0f}  low: {gas[i]['low']}  high: {gas[i]['high']}")
