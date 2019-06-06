#!/usr/bin/python3

import json
from pathlib import Path
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
        self.total = total - count
        self.total_time = time.time()
        print("\nRunning {0[module]}{1}{0} - {2} test{3} ({4}/{5})".format(
            color,
            path,
            self.total,
            "s" if total != 1 else "",
            self.grand_count,
            self.grand_total
        ))

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
    print("{0}{1}{2}: {3}".format(color(CPRINT_TYPES[type_]), type_, color, msg))


def display_report(coverage_files, report_path=None):
    coverage_eval = coverage.merge_files(coverage_files)
    report = {
        'highlights': coverage.get_highlights(coverage_eval),
        'coverage': coverage.get_totals(coverage_eval),
        'sha1': {}  # TODO
    }
    print("\nCoverage analysis:")
    for name in sorted(report['coverage']):
        totals = report['coverage'][name]['totals']
        pct = _pct(totals['statements'], totals['branches'])
        c = color(next(i[1] for i in COVERAGE_COLORS if pct <= i[0]))
        print("\n  contract: {0[contract]}{1}{0} - {2}{3:.1%}{0}".format(color, name, c, pct))
        cov = report['coverage'][name]
        for fn_name, count in cov['statements'].items():
            branch = cov['branches'][fn_name] if fn_name in cov['branches'] else (0, 0, 0)
            pct = _pct(count, branch)
            print("    {0[contract_method]}{1}{0} - {2}{3:.1%}{0}".format(
                color,
                fn_name,
                color(next(i[1] for i in COVERAGE_COLORS if pct <= i[0])),
                pct
            ))
    if not report_path:
        return
    report_path = Path(report_path)
    if report_path.is_dir():

        filename = "coverage-"+time.strftime('%d%m%y')+"{}.json"
        count = len(list(report_path.glob(filename.format('*'))))
        report_path = report_path.joinpath(filename.format("-"+str(count) if count else ""))
    json.dump(report, report_path.open('w'), sort_keys=True, indent=2, default=sorted)
    print("\nCoverage report saved at {}".format(report_path.relative_to(sys.path[0])))


def _pct(statement, branch):
    pct = statement[0]/statement[1]
    if branch[-1]:
        pct = (pct + (branch[0]+branch[1])/(branch[2]*2)) / 2
    return pct


def display_gas_profile():
    print('\nGas Profile:')
    gas = history.gas_profile
    for i in sorted(gas):
        print("{0} -  avg: {1[avg]:.0f}  low: {1[low]}  high: {1[high]}".format(i, gas[i]))
