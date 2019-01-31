from copy import deepcopy
from docopt import docopt
import os
import re
import shutil
import sys
import json

from lib.test import run_test
from lib.components.network import Network
from lib.components.bytecode import get_coverage_map
from lib.services import color
from lib.services.compiler import compile_contracts

COVERAGE_COLORS = [
    (0.5, "bright red"),
    (0.85, "bright yellow"),
    (1, "bright green")
]

__doc__ = """Usage: brownie coverage [<filename>] [options]

Arguments:
  <filename>         Only run tests from a specific file

Options:
  --help             Display this message
  --verbose          Enable verbose reporting

Coverage will modify the contracts and run your unit tests to get estimate
of how much coverage you have.  so simple..."""


def main():
    args = docopt(__doc__)

    if args['<filename>']:
        name = args['<filename>'].replace(".py", "")
        if not os.path.exists("tests/{}.py".format(name)):
            sys.exit(
                "{0[error]}ERROR{0}: Cannot find".format(color) +
                " {0[module]}tests/{1}.py{0}".format(color, name)
            )
        test_files = [name]
    else:
        test_files = [i[:-3] for i in os.listdir("tests") if i[-3:] == ".py"]
        test_files.remove('__init__')
    
    compiled = deepcopy(compile_contracts())
    fn_map, line_map = get_coverage_map(compiled)

    network = Network()
    for filename in test_files:
        history, tb = run_test(filename, network)
        if tb:
            sys.exit(
                "\n{0[error]}ERROR{0}: Cannot ".format(color) +
                "calculate coverage while tests are failing\n"
            )
        for tx in history:
            if not tx.receiver:
                continue
            for i in range(len(tx.trace)):
                t = tx.trace[i]
                pc = t['pc']
                name = t['contractName']
                if not name:
                    continue
                try:
                    # find the function map item and record the tx
                    fn = next(i for i in fn_map[name] if pc in i['pc'])
                    fn['tx'].add(tx)
                    if t['op']!="JUMPI":
                        # if not a JUMPI, find the line map item and record
                        ln = next(i for i in line_map[name] if pc in i['pc'])
                        ln['tx'].add(tx)
                        continue
                    # if a JUMPI, we need to have hit the jump pc AND a related opcode
                    ln = next(i for i in line_map[name] if pc==i['jump'])
                    if tx not in ln['tx']:
                        continue
                    # if the next opcode is not pc+1, the JUMPI was executed truthy
                    key = 'false' if tx.trace[i+1]['pc'] == pc+1 else 'true'
                    ln[key].add(tx)
                # pc didn't exist in map
                except StopIteration:
                    continue

    for ln in [x for v in line_map.values() for x in v]:
        if ln['jump']:
            ln['jump'] = [len(ln.pop('true')), len(ln.pop('false'))]
        ln['count'] = len(ln.pop('tx'))
        del ln['pc']

    for contract in fn_map:
        for fn in fn_map[contract].copy():
            fn['count'] = len(fn.pop('tx'))
            del fn['pc']
            line_fn = [i for i in line_map[contract] if i['method']==fn['method']]
            if not fn['count'] or not [i for i in line_fn if i['count']]:
                for ln in line_fn:
                    line_map[contract].remove(ln)
            elif line_fn:
                fn_map[contract].remove(fn)
        fn_map[contract].extend(line_map[contract])

    json.dump(fn_map, open("build/coverage.json", "w"), sort_keys=True, indent=4)
    print("\nCoverage analysis complete!")
    for contract in fn_map:
        fn_list = sorted(set(i['method'] for i in fn_map[contract] if i['method']))
        if not fn_list:
            continue
        print("\n  contract: {0[contract]}{1}{0}".format(color, contract))
        for fn in fn_list:
            map_ = [i for i in fn_map[contract] if i['method']==fn]
            count = 0
            for i in map_:
                if not i['count']:
                    continue
                if not i['jump']:
                    count+=1
                    continue
                if i['jump'][0]:
                    count+=1
                if i['jump'][1]:
                    count+=1
            total = sum([1 if not i['jump'] else 2 for i in map_])
            pct = count / total
            c = next(i[1] for i in COVERAGE_COLORS if pct<=i[0])
            print("    {0[contract_method]}{1}{0} - {2}{3:.1%}{0}".format(
                color, fn, color(c), pct
            ))
    print("\nDetailed results saved to {0[string]}builld/coverage.json{0}".format(color))