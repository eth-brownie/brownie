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
    merge_coverage,
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
        history = TxHistory()
        history._revert_lock = True

    test_files = get_test_files(args['<filename>'])
    if len(test_files) == 1 and args['<range>']:
        try:
            idx = args['<range>']
            if ':' in idx:
                idx = slice(*[int(i)-1 for i in idx.split(':')])
            else:
                idx = slice(int(idx)-1, int(idx))
        except Exception:
            sys.exit("{0[error]}ERROR{0}: Invalid range. Must be an integer or slice (eg. 1:4)".format(color))
    elif args['<range>']:
        sys.exit("{0[error]}ERROR:{0} Cannot specify a range when running multiple tests files.".format(color))
    else:
        idx = slice(0, None)

    network.connect(ARGV['network'])
    coverage_files = []
    traceback_info = []

    try:
        for filename in test_files:
            coverage_json = Path(CONFIG['folders']['project'])
            coverage_json = coverage_json.joinpath("build/coverage"+filename[5:]+".json")
            coverage_files.append(coverage_json)
            if coverage_json.exists():
                coverage_eval = json.load(coverage_json.open())['coverage']
                if ARGV['update'] and (coverage_eval or not ARGV['coverage']):
                    continue
            else:
                coverage_eval = {}
                for p in list(coverage_json.parents)[::-1]:
                    if not p.exists():
                        p.mkdir()

            tb, cov = run_test(filename, network, idx)
            if tb:
                traceback_info += tb
                if coverage_json.exists():
                    coverage_json.unlink()
                continue

            if ARGV['coverage']:
                coverage_eval = cov

            build_files = set(Path('build/contracts/{}.json'.format(i)) for i in coverage_eval)
            coverage_eval = {
                'coverage': coverage_eval,
                'sha1': dict((str(i), Build()[i.stem]['bytecodeSha1']) for i in build_files)
            }
            if args['<range>']:
                continue

            test_path = Path(filename+".py")
            coverage_eval['sha1'][str(test_path)] = get_ast_hash(test_path)
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
        if traceback_info:
            print("\n{0[error]}WARNING{0}: {1} test{2} failed.{0}".format(
                color, len(traceback_info), "s" if len(traceback_info) > 1 else ""
            ))
            for err in traceback_info:
                print("\nException info for {0[0]}:\n{0[1]}".format(err))
            sys.exit()

    print("\n{0[success]}SUCCESS{0}: All tests passed.".format(color))

    if args['--coverage']:
        coverage_eval = merge_coverage(coverage_files)
        display_report(coverage_eval)
        filename = "coverage-"+time.strftime('%d%m%y')+"{}.json"
        path = Path(CONFIG['folders']['project']).joinpath('reports')
        count = len(list(path.glob(filename.format('*'))))
        path = path.joinpath(filename.format("-"+str(count) if count else ""))
        json.dump(
            generate_report(coverage_eval),
            path.open('w'),
            sort_keys=True,
            indent=2,
            default=sorted
        )
        print("Coverage report saved at {}".format(path.relative_to(CONFIG['folders']['project'])))

    if args['--gas']:
        print('\nGas Profile:')
        for i in sorted(transaction.gas_profile):
            print("{0} -  avg: {1[avg]:.0f}  low: {1[low]}  high: {1[high]}".format(i, transaction.gas_profile[i]))


def get_test_files(path):
    if not path:
        path = ""
    if path[:6] != "tests/":
        path = "tests/" + path
    path = Path(CONFIG['folders']['project']).joinpath(path)
    if not path.is_dir():
        if not path.suffix:
            path = Path(str(path)+".py")
        if not path.exists():
            sys.exit("{0[error]}ERROR{0}: Cannot find {0[module]}tests/{1}{0}".format(color, path.name))
        result = [path]
    else:
        result = [i for i in path.glob('**/*.py') if i.name[0] != "_" and "/_" not in str(i)]
    return [str(i.relative_to(CONFIG['folders']['project']))[:-3] for i in result]


def run_test(filename, network, idx):
    network.rpc.reset()
    if type(CONFIG['test']['gas_limit']) is int:
        network.gas_limit(CONFIG['test']['gas_limit'])

    module = importlib.import_module(filename.replace(os.sep, '.'))
    code = Path(filename+".py").open().read()
    test_names = re.findall(r'\ndef[\s ]{1,}([^_]\w*)[\s ]*\([^)]*\)', code)
    duplicates = set([i for i in test_names if test_names.count(i) > 1])
    if duplicates:
        raise ValueError("tests/{}.py contains multiple tests of the same name: {}".format(
            filename,
            ", ".join(duplicates)
        ))

    if not test_names:
        print("\n{0[error]}WARNING{0}: No test functions in {0[module]}{1}.py{0}".format(color, filename))
        return [], {}

    if ARGV['coverage']:
        ARGV['always_transact'] = True
        always_transact = True

    traceback_info = []
    if 'setup' in test_names:
        test_names.remove('setup')
        fn, default_args = _get_fn(module, 'setup')

        if default_args['skip'] is True or (default_args['skip'] == "coverage" and ARGV['coverage']):
            return [], {}
        p = TestPrinter(filename, 0, len(test_names))
        traceback_info += run_test_method(fn, default_args, p)
        if traceback_info:
            return traceback_info, {}
    else:
        p = TestPrinter(filename, 1, len(test_names))
        default_args = FalseyDict()
    network.rpc.snapshot()
    for t in test_names[idx]:
        network.rpc.revert()
        fn, fn_args = _get_fn(module, t)
        args = default_args.copy()
        args.update(fn_args)
        traceback_info += run_test_method(fn, args, p)
        if ARGV['coverage']:
            ARGV['always_transact'] = always_transact
        if traceback_info and traceback_info[-1][2] == ReadTimeout:
            print("{0[error]}WARNING{0}: RPC crashed, terminating test".format(color))
            network.rpc.kill(False)
            network.rpc.launch(CONFIG['active_network']['test-rpc'])
            break
    if not traceback_info and ARGV['coverage']:
        p.start("Evaluating test coverage")
        coverage_eval = analyze_coverage(TxHistory().copy())
        p.stop()
        return traceback_info, coverage_eval
    return traceback_info, {}


def _get_fn(module, name):
    fn = getattr(module, name)
    if not fn.__defaults__:
        return fn, FalseyDict()
    return fn, FalseyDict(zip(
        fn.__code__.co_varnames[:len(fn.__defaults__)],
        fn.__defaults__
    ))


def run_test_method(fn, args, p):
    desc = fn.__doc__ or fn.__name__
    if args['skip'] is True or (args['skip'] == "coverage" and ARGV['coverage']):
        p.skip(desc)
        return []
    p.start(desc)
    try:
        if ARGV['coverage'] and 'always_transact' in args:
            ARGV['always_transact'] = args['always_transact']
        fn()
        if ARGV['coverage']:
            ARGV['always_transact'] = True
        if args['pending']:
            raise ExpectedFailing("Test was expected to fail")
        p.stop()
        return []
    except Exception as e:
        p.stop(e, args['pending'])
        if type(e) != ExpectedFailing and args['pending']:
            return []
        return [(
            fn.__name__,
            color.format_tb(
                sys.exc_info(),
                Path(sys.modules[fn.__module__].__file__).relative_to(CONFIG['folders']['project'])
            ),
            type(e)
        )]


def display_report(coverage_eval):
    print("\nCoverage analysis:\n")
    for contract in coverage_eval:
        print("  contract: {0[contract]}{1}{0}".format(color, contract))
        for fn_name, pct in [(x, v[x]['pct']) for v in coverage_eval[contract].values() for x in v]:
            c = next(i[1] for i in COVERAGE_COLORS if pct <= i[0])
            print("    {0[contract_method]}{1}{0} - {2}{3:.1%}{0}".format(
                color, fn_name, color(c), pct
            ))
        print()


class TestPrinter:

    def __init__(self, path, count, total):
        self.path = path
        self.count = count
        self.total = total
        print("\nRunning {0[module]}{1}.py{0} - {2} test{3}".format(
            color,
            path,
            total,
            "s" if total != 1 else ""
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

    def _print(self, msg, symbol=" ", symbol_color="success", main_color=None):
        sys.stdout.write("\r {}{}{} {} - {}".format(
            color(symbol_color),
            symbol,
            color(main_color),
            self.count,
            msg
        ))
        sys.stdout.flush()
