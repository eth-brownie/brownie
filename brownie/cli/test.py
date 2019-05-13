#!/usr/bin/python3

from docopt import docopt
import importlib
import json
import os
from pathlib import Path
import re
from requests.exceptions import ReadTimeout
import sys
import time

from brownie.cli.utils import color
from brownie.test.coverage import (
    analyze_coverage,
    merge_coverage_eval,
    merge_coverage_files,
    generate_report
)
from brownie.exceptions import ExpectedFailing
import brownie.network as network
from brownie.network.history import TxHistory
import brownie.network.transaction as transaction
from brownie.project.build import Build, get_ast_hash
from brownie.types import FalseyDict
from brownie._config import ARGV, CONFIG

COVERAGE_COLORS = [
    (0.5, "bright red"),
    (0.85, "bright yellow"),
    (1, "bright green")
]

WARN = "{0[error]}WARNING{0}: ".format(color)
ERROR = "{0[error]}ERROR{0}: ".format(color)

history = TxHistory()

__doc__ = """Usage: brownie test [<filename>] [<range>] [options]

Arguments:
  <filename>              Only run tests from a specific file or folder
  <range>                 Number or range of tests to run from file

Options:

  --update -u             Only run tests where changes have occurred
  --coverage -c           Evaluate test coverage
  --gas -g                Display gas profile for function calls
  --verbose -v            Enable verbose reporting
  --tb -t                 Show entire python traceback on exceptions
  --help -h               Display this message

By default brownie runs every script found in the tests folder as well as any
subfolders. Files and folders beginning with an underscore will be skipped."""


def main():
    args = docopt(__doc__)
    ARGV._update_from_args(args)
    if ARGV['coverage']:
        ARGV['always_transact'] = True
        history._revert_lock = True

    test_paths = get_test_paths(args['<filename>'])
    coverage_files, test_data = get_test_data(test_paths)

    if len(test_paths) == 1 and args['<range>']:
        try:
            idx = args['<range>']
            if ':' in idx:
                idx = slice(*[int(i)-1 for i in idx.split(':')])
            else:
                idx = slice(int(idx)-1, int(idx))
            if 'setup' in test_data[0][4]:
                test_data[0][4].remove('setup')
                test_data[0][4] = ['setup'] + test_data[0][4][idx]
            else:
                test_data[0][4] = ['setup'] + test_data[0][4][idx]
        except Exception:
            sys.exit(ERROR+"Invalid range. Must be an integer or slice (eg. 1:4)")
    elif args['<range>']:
        sys.exit(ERROR+"Cannot specify a range when running multiple tests files.")

    if not test_data:
        print("No tests to run.")
    else:
        run_test_modules(test_data, not args['<range>'])
    if ARGV['coverage']:
        display_report(coverage_files, not args['<range>'])
    if ARGV['gas']:
        display_gas_profile()


def get_test_paths(path):
    if not path:
        path = ""
    if path[:6] != "tests/":
        path = "tests/" + path
    path = Path(CONFIG['folders']['project']).joinpath(path)
    if path.is_dir():
        return [i for i in path.glob('**/*.py') if i.name[0] != "_" and "/_" not in str(i)]
    if not path.suffix:
        path = Path(str(path)+".py")
    if not path.exists():
        sys.exit(ERROR+"Cannot find {0[module]}tests/{1}{0}".format(color, path.name))
    return [path]


def get_test_data(test_paths):
    coverage_files = []
    test_data = []
    project = Path(CONFIG['folders']['project'])
    build_path = project.joinpath('build/coverage')
    for path in test_paths:
        path = path.relative_to(project)
        coverage_json = build_path.joinpath(path.parent.relative_to('tests'))
        coverage_json = coverage_json.joinpath(path.stem+".json")
        coverage_files.append(coverage_json)
        if coverage_json.exists():
            coverage_eval = json.load(coverage_json.open())['coverage']
            if ARGV['update'] and (coverage_eval or not ARGV['coverage']):
                continue
        else:
            coverage_eval = {}
            for p in list(coverage_json.parents)[::-1]:
                p.mkdir(exist_ok=True)
        module_name = str(path)[:-3].replace(os.sep, '.')
        module = importlib.import_module(module_name)
        test_names = re.findall(r'\ndef[\s ]{1,}([^_]\w*)[\s ]*\([^)]*\)', path.open().read())
        if not test_names:
            print("\n{0}No test functions in {1[module]}{2}.py{1}".format(WARN, color, path))
            continue
        duplicates = set([i for i in test_names if test_names.count(i) > 1])
        if duplicates:
            raise ValueError("{} contains multiple test methods of the same name: {}".format(
                path,
                ", ".join(duplicates)
            ))
        if 'setup' in test_names:
            fn, args = _get_fn(module, 'setup')
            if args['skip'] is True or (args['skip'] == "coverage" and ARGV['coverage']):
                continue
        test_data.append((module, coverage_json, coverage_eval, test_names))
    return coverage_files, test_data


def run_test_modules(test_data, save):
    TestPrinter.grand_total = len(test_data)
    count = sum([len([x for x in i[3] if x != "setup"]) for i in test_data])
    print("Running {} tests across {} modules.".format(count, len(test_data)))
    network.connect(ARGV['network'])
    for key in ('broadcast_reverting_tx', 'gas_limit'):
        CONFIG['active_network'][key] = CONFIG['test'][key]
    if not CONFIG['active_network']['broadcast_reverting_tx']:
        print("{0[error]}WARNING{0}: Reverting transactions will NOT be broadcasted.".format(color))
    traceback_info = []
    start_time = time.time()
    try:
        for (module, coverage_json, coverage_eval, test_names) in test_data:
            tb, cov = run_test(module, network, test_names)
            if tb:
                traceback_info += tb
                if coverage_json.exists():
                    coverage_json.unlink()
                continue

            if not save:
                continue
            if ARGV['coverage']:
                coverage_eval = cov

            build_files = set(Path('build/contracts/{}.json'.format(i)) for i in coverage_eval)
            coverage_eval = {
                'coverage': coverage_eval,
                'sha1': dict((str(i), Build()[i.stem]['bytecodeSha1']) for i in build_files)
            }
            coverage_eval['sha1'][module.__file__] = get_ast_hash(module.__file__)
            json.dump(
                coverage_eval,
                coverage_json.open('w'),
                sort_keys=True,
                indent=2,
                default=sorted
            )
    except KeyboardInterrupt:
        print("\n\nTest execution has been terminated by KeyboardInterrupt.")
        sys.exit()
    finally:
        print("\nTotal runtime: {:.4f}s".format(time.time() - start_time))
        if traceback_info:
            print("{0}{1} test{2} failed.".format(
                WARN,
                len(traceback_info),
                "s" if len(traceback_info) > 1 else ""
            ))
            for err in traceback_info:
                print("\nTraceback for {0[0]}:\n{0[1]}".format(err))
            sys.exit()
    print("{0[success]}SUCCESS{0}: All tests passed.".format(color))


def run_test(module, network, test_names):
    network.rpc.reset()

    if 'setup' in test_names:
        test_names.remove('setup')
        fn, default_args = _get_fn(module, 'setup')

        if default_args['skip'] is True or (
            default_args['skip'] == "coverage" and ARGV['coverage']
        ):
            return [], {}
        p = TestPrinter(module.__file__, 0, len(test_names))
        tb, coverage_eval = run_test_method(fn, default_args, {}, p)
        if tb:
            return tb, {}
    else:
        p = TestPrinter(module.__file__, 1, len(test_names))
        default_args = FalseyDict()
        coverage_eval = {}
    network.rpc.snapshot()
    traceback_info = []
    for t in test_names:
        network.rpc.revert()
        fn, fn_args = _get_fn(module, t)
        args = default_args.copy()
        args.update(fn_args)
        tb, coverage_eval = run_test_method(fn, args, coverage_eval, p)
        traceback_info += tb
        if tb and tb[0][2] == ReadTimeout:
            print(WARN+"RPC crashed, terminating test")
            network.rpc.kill(False)
            network.rpc.launch(CONFIG['active_network']['test-rpc'])
            break
    if traceback_info and ARGV['coverage']:
        coverage_eval = {}
    p.finish()
    return traceback_info, coverage_eval


def run_test_method(fn, args, coverage_eval, p):
    desc = fn.__doc__ or fn.__name__
    if args['skip'] is True or (args['skip'] == "coverage" and ARGV['coverage']):
        p.skip(desc)
        return [], coverage_eval
    p.start(desc)
    try:
        if ARGV['coverage'] and 'always_transact' in args:
            ARGV['always_transact'] = args['always_transact']
        fn()
        if ARGV['coverage']:
            ARGV['always_transact'] = True
            coverage_eval = merge_coverage_eval(
                coverage_eval,
                analyze_coverage(history.copy())
            )
            history.clear()
        if args['pending']:
            raise ExpectedFailing("Test was expected to fail")
        p.stop()
        return [], coverage_eval
    except Exception as e:
        p.stop(e, args['pending'])
        if type(e) != ExpectedFailing and args['pending']:
            return [], coverage_eval
        path = Path(sys.modules[fn.__module__].__file__).relative_to(CONFIG['folders']['project'])
        path = "{0[module]}{1}.{0[callable]}{2}{0}".format(color, str(path)[:-3], fn.__name__)
        tb = color.format_tb(sys.exc_info(), sys.modules[fn.__module__].__file__)
        return [(path, tb, type(e))], coverage_eval


def display_report(coverage_files, save):
    coverage_eval = merge_coverage_files(coverage_files)
    report = generate_report(coverage_eval)
    print("\nCoverage analysis:")
    for name in sorted(coverage_eval):
        pct = coverage_eval[name].pop('pct')
        c = color(next(i[1] for i in COVERAGE_COLORS if pct <= i[0]))
        print("\n  contract: {0[contract]}{1}{0} - {2}{3:.1%}{0}".format(color, name, c, pct))
        for fn_name, pct in [(x, v[x]['pct']) for v in coverage_eval[name].values() for x in v]:
            print("    {0[contract_method]}{1}{0} - {2}{3:.1%}{0}".format(
                color,
                fn_name,
                color(next(i[1] for i in COVERAGE_COLORS if pct <= i[0])),
                pct
            ))
    if not save:
        return
    filename = "coverage-"+time.strftime('%d%m%y')+"{}.json"
    path = Path(CONFIG['folders']['project']).joinpath('reports')
    count = len(list(path.glob(filename.format('*'))))
    path = path.joinpath(filename.format("-"+str(count) if count else ""))
    json.dump(report, path.open('w'), sort_keys=True, indent=2, default=sorted)
    print("\nCoverage report saved at {}".format(path.relative_to(CONFIG['folders']['project'])))


def display_gas_profile():
    print('\nGas Profile:')
    gas = transaction.gas_profile
    for i in sorted(gas):
        print("{0} -  avg: {1[avg]:.0f}  low: {1[low]}  high: {1[high]}".format(i, gas[i]))


def _get_fn(module, name):
    fn = getattr(module, name)
    if not fn.__defaults__:
        return fn, FalseyDict()
    return fn, FalseyDict(zip(
        fn.__code__.co_varnames[:len(fn.__defaults__)],
        fn.__defaults__
    ))


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
            total,
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
