#!/usr/bin/python3

from docopt import docopt
from hashlib import sha1
import json
from pathlib import Path
import sys

from brownie.cli.test import get_test_files, run_test
from brownie.test.coverage import merge_coverage, analyze_coverage
from brownie.cli.utils import color
import brownie.network as network
import brownie._config as config

CONFIG = config.CONFIG

COVERAGE_COLORS = [
    (0.5, "bright red"),
    (0.85, "bright yellow"),
    (1, "bright green")
]

__doc__ = """Usage: brownie coverage [<filename>] [<range>] [options]

Arguments:
  <filename>          Only run tests from a specific file or folder
  <range>             Number or range of tests to run from file

Options:
  --update            Only evaluate coverage on changed contracts/tests
  --always-transact   Perform all contract calls as transactions
  --verbose           Enable verbose reporting
  --tb                Show entire python traceback on exceptions
  --help              Display this message

Runs unit tests and analyzes the transaction stack traces to estimate
current test coverage. Results are saved to build/coverage.json"""


def main():
    args = docopt(__doc__)

    test_files = get_test_files(args['<filename>'])
    if len(test_files)==1 and args['<range>']:
        try:
            idx = args['<range>']
            if ':' in idx:
                idx = slice(*[int(i)-1 for i in idx.split(':')])
            else:
                idx = slice(int(idx)-1,int(idx))
        except:
            sys.exit("{0[error]}ERROR{0}: Invalid range. Must be an integer or slice (eg. 1:4)".format(color))
    elif args['<range>']:
        sys.exit("{0[error]}ERROR:{0} Cannot specify a range when running multiple tests files.".format(color))
    else:
        idx = slice(0, None)

    network.connect(config.ARGV['network'], True)

    if args['--always-transact']:
        CONFIG['test']['always_transact'] = True
    print("Contract calls will be handled as: {0[value]}{1}{0}".format(
        color,
        "transactions" if CONFIG['test']['always_transact'] else "calls"
    ))

    coverage_files = []

    for filename in test_files:

        coverage_json = Path(CONFIG['folders']['project'])
        coverage_json = coverage_json.joinpath("build/coverage"+filename[5:]+".json")
        coverage_files.append(coverage_json)
        if config.ARGV['update'] and coverage_json.exists():
            continue
        for p in list(coverage_json.parents)[::-1]:
            if not p.exists():
                p.mkdir()

        history, tb = run_test(filename, network, idx)
        if tb:
            if coverage_json.exists():
                coverage_json.unlink()
            continue

        coverage_eval = analyze_coverage(history)
        build_folder = Path(CONFIG['folders']['project']).joinpath('build/contracts')
        build_files = set(build_folder.joinpath(i+'.json') for i in coverage_eval)
        coverage_eval = {
            'contracts': coverage_eval,
            'sha1': dict((
                str(i),
                # hash of bytecode without final metadata
                sha1(json.load(i.open())['bytecode'][:-68].encode()).hexdigest()
            ) for i in build_files)
        }
        if args['<range>']:
            continue

        test_path = Path(CONFIG['folders']['project']).joinpath(filename+".py")
        coverage_eval['sha1'][str(test_path)] = sha1(test_path.open('rb').read()).hexdigest()

        json.dump(
            coverage_eval,
            coverage_json.open('w'),
            sort_keys=True,
            indent=4,
            default=sorted
        )

    print("\nCoverage analysis complete!\n")
    coverage_eval = merge_coverage(coverage_files)

    for contract in coverage_eval:
        print("  contract: {0[contract]}{1}{0}".format(color, contract))
        for fn_name, pct in [(x,v[x]['pct']) for v in coverage_eval[contract].values() for x in v]:
            c = next(i[1] for i in COVERAGE_COLORS if pct<=i[0])
            print("    {0[contract_method]}{1}{0} - {2}{3:.1%}{0}".format(
                color, fn_name, color(c), pct
            ))
        print()
    print("\nDetailed reports saved in {0[string]}build/coverage{0}".format(color))