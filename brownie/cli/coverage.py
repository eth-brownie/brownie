#!/usr/bin/python3

from copy import deepcopy
from docopt import docopt
from hashlib import sha1
from pathlib import Path
import sys
import json

from brownie.cli.test import get_test_files, run_test
from brownie.test.coverage import merge_coverage
from brownie.cli.utils import color
import brownie.network as network
from brownie.utils.compiler import get_build
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
  --help              Display this message
  --verbose           Enable verbose reporting
  --tb                Show entire python traceback on exceptions
  --always-transact   Perform all contract calls as transactions

Runs unit tests and analyzes the transaction stack traces to estimate
current test coverage. Results are saved to build/coverage.json"""


def main():
    args = docopt(__doc__)

    test_files = get_test_files(args['<filename>'])
    coverage_files = []
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

    # remove coverage data where hashes have changed
    coverage_folder = Path(CONFIG['folders']['project']).joinpath("build/coverage")
    for coverage_json in list(coverage_folder.glob('**/*.json')):
        dependents = json.load(coverage_json.open())['sha1']
        for path, hash_ in dependents.items():
            path = Path(path)
            if not path.exists() or sha1(path.open('rb').read()).hexdigest() != hash_:
                print(path)
                coverage_json.unlink()
                break

    network.connect(config.ARGV['network'], True)

    if args['--always-transact']:
        CONFIG['test']['always_transact'] = True
    print("Contract calls will be handled as: {0[value]}{1}{0}".format(
        color,
        "transactions" if CONFIG['test']['always_transact'] else "calls"
    ))

    for filename in test_files:
        history, tb = run_test(filename, network, idx)
        if tb:
            sys.exit(
                "\n{0[error]}ERROR{0}: Cannot ".format(color) +
                "calculate coverage while tests are failing\n"
            )
        coverage_map = {}
        coverage_eval = {}
        for tx in history:
            if not tx.receiver:
                continue
            for i in range(len(tx.trace)):
                t = tx.trace[i]
                pc = t['pc']
                name = t['contractName']
                source = t['source']['filename']
                if not name or not source:
                    continue
                if name not in coverage_map:
                    coverage_map[name] = get_build(name)['coverageMap']
                    coverage_eval[name] = dict((i,{}) for i in coverage_map[name])
                try:
                    # find the function map item and record the tx
                    
                    fn = next(v for k,v in coverage_map[name][source].items() if pc in v['fn']['pc'])
                    fn['fn'].setdefault('tx',set()).add(tx)
                    if t['op']!="JUMPI":
                        # if not a JUMPI, find the line map item and record
                        next(i for i in fn['line'] if pc in i['pc']).setdefault('tx',set()).add(tx)
                        continue
                    # if a JUMPI, we need to have hit the jump pc AND a related opcode
                    ln = next(i for i in fn['line'] if pc==i['jump'])
                    for key in ('tx', 'true', 'false'):
                        ln.setdefault(key, set())
                    if tx not in ln['tx']:
                        continue
                    # if the next opcode is not pc+1, the JUMPI was executed truthy
                    key = 'false' if tx.trace[i+1]['pc'] == pc+1 else 'true'
                    ln[key].add(tx)
                # pc didn't exist in map
                except StopIteration:
                    continue

        for contract, source, fn_name, maps in [(k,w,y,z) for k,v in coverage_map.items() for w,x in v.items() for y,z in x.items()]:
            fn = maps['fn']
            if 'tx' not in fn or not fn['tx']:
                coverage_eval[contract][source][fn_name] = {'pct':0}
                continue
            for ln in maps['line']:
                if 'tx' not in ln:
                    ln['count'] = 0
                    continue
                if ln['jump']:
                    ln['jump'] = [len(ln.pop('true')), len(ln.pop('false'))]
                ln['count'] = len(ln.pop('tx'))

            if not [i for i in maps['line'] if i['count']]:
                coverage_eval[contract][source][fn_name] = {'pct':0}
                continue

            count = 0
            coverage = {'line':set(), 'true':set(), 'false':set()}
            for c,i in enumerate(maps['line']):
                if not i['count']:
                    continue
                if not i['jump'] or False not in i['jump']:
                    coverage['line'].add(c)
                    count+=2 if i['jump'] else 1
                    continue
                if i['jump'][0]:
                    coverage['true'].add(c)
                    count+=1
                if i['jump'][1]:
                    coverage['false'].add(c)
                    count+=1
            pct = count / maps['total']
            if count == maps['total']:
                coverage_eval[contract][source][fn_name] = {'pct': 1}
            else:
                coverage['pct']=round(count/maps['total'],2)
                coverage_eval[contract][source][fn_name] = coverage

        contract_files = set(x for i in coverage_eval.values() for x in i)
        coverage_eval = {
            'contracts': coverage_eval,
            'sha1': dict((i, sha1(open(i, 'rb').read()).hexdigest()) for i in contract_files)
        }
        test_path = Path(CONFIG['folders']['project']).joinpath(filename+".py")
        coverage_eval['sha1'][str(test_path)] = sha1(test_path.open('rb').read()).hexdigest()

        path = Path(CONFIG['folders']['project'])
        path = path.joinpath("build/coverage"+filename[5:]+".json")

        coverage_files.append(path)

        for p in list(path.parents)[::-1]:
            if not p.exists():
                p.mkdir()
        json.dump(
            coverage_eval,
            path.open('w'),
            sort_keys=True,
            indent=4,
            default=sorted
        )

    # TODO - beyond here things are still broken
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