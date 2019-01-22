from copy import deepcopy
from docopt import docopt
import os
import re
import shutil   
import sys

from lib.test import run_test
from lib.services import color
from lib.services.compiler import compile_contracts


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
                "{0[bright red]}ERROR{0}: Cannot find".format(color) +
                " {0[bright yellow]}tests/{1}.py{0}".format(color, name)
            )
        test_files = [name]
    else:
        test_files = [i[:-3] for i in os.listdir("tests") if i[-3:] == ".py"]
        test_files.remove('__init__')
    
    compiled = deepcopy(compile_contracts())
    for i in compiled:
        compiled[i] = dict((int(k),0) for k,v in compiled[i]['pcMap'].items() if v['contract'])
    for filename in test_files:
        history, tb = run_test(filename)
        if tb:
            sys.exit(
                "\n{0[error]}ERROR{0}: Cannot ".format(color) +
                "calculate coverage while tests are failing\n\n" + 
                "Exception info for {}:\n{}".format(tb[0], tb[1])
            )
        for trace in [x for i in history[1:] for x in i.trace]:
            c = compiled[trace['contractName']]
            if trace['pc'] in c:
                c[trace['pc']] += 1
    results = [x for v in compiled.values() for x in v.values()]
    print(results.count(0)/len(results))

    # pcMap doesn't work on constructor since it's only generated for deployed bytecode