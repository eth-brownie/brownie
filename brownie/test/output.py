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

CPRINT_TYPES = {
    'WARNING': 'error',
    'ERROR': 'error',
    'SUCCESS': 'success'
}


class TestPrinter:

    grand_count = 1
    grand_total = 0

    def __init__(self, path, count, total):
        self.path = path
        self.count = count
        self.total = total
        self.total_time = time.time()
        print("\nRunning {0[module]}{1}{0} - {2} test{3} ({4}/{5})".format(
            color,
            path,
            self.total,
            "s" if total != 1 else "",
            self.grand_count,
            self.grand_total
        ))

    @classmethod
    def set_grand_total(cls, total):
        cls.grand_total = total

    def skip(self, description):
        self._print(
            "{0} ({1[pending]}skipped{1[dull]})\n".format(description, color),
            "\u229d",
            "pending",
            "dull"
        )
        self.count += 1

    def start(self, description):
        self.desc = description
        self._print("{} ({}/{})...".format(description, self.count, self.total))
        self.time = time.time()

    def stop(self, err=None, expect=False):
        if not err:
            self._print("{} ({:.4f}s)  \n".format(self.desc, time.time() - self.time), "\u2713")
        else:
            err = type(err).__name__
            color_str = 'success' if expect and err != "ExpectedFailing" else 'error'
            symbol = '\u2717' if err in ("AssertionError", "VirtualMachineError") else '\u203C'
            msg = "{} ({}{}{})\n".format(
                self.desc,
                color(color_str),
                err,
                color('dull')
            )
            self._print(msg, symbol, color_str, "dull")
        self.count += 1

    def finish(self):
        print("Completed {0[module]}{1}{0} ({2:.4f}s)".format(
            color,
            self.path,
            time.time() - self.total_time
        ))
        TestPrinter.grand_count += 1

    def _print(self, msg, symbol=" ", symbol_color="success", main_color=None):
        sys.stdout.write("\r {}{}{} {} - {}{}".format(
            color(symbol_color),
            symbol,
            color(main_color),
            self.count,
            msg,
            color
        ))
        sys.stdout.flush()


def cprint(type_, msg):
    '''Prepends a message with a colored tag and outputs it to the console.'''
    print("{0}{1}{2}: {3}".format(color(CPRINT_TYPES[type_]), type_, color, msg))


def coverage_totals(coverage_eval):
    '''Formats and prints a coverage evaluation report to the console.

    Args:
        coverage_eval: coverage evaluation dict

    Returns: None'''
    totals = coverage.get_totals(coverage_eval)
    print("\nCoverage analysis:")
    for name in sorted(totals):
        pct = _pct(totals[name]['totals']['statements'], totals[name]['totals']['branches'])
        print("\n  contract: {0[contract]}{1}{0} - {2}{3:.1%}{0}".format(
            color, name, _cov_color(pct), pct
        ))
        cov = totals[name]
        for fn_name, count in cov['statements'].items():
            branch = cov['branches'][fn_name] if fn_name in cov['branches'] else (0, 0, 0)
            pct = _pct(count, branch)
            print("    {0[contract_method]}{1}{0} - {2}{3:.1%}{0}".format(
                color, fn_name, _cov_color(pct), pct
            ))


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
        print("{0} -  avg: {1[avg]:.0f}  low: {1[low]}  high: {1[high]}".format(i, gas[i]))
