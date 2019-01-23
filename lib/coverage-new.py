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
    pc = {}
    source = {}
    for i in compiled:
        pc[i] = compiled[i]['pcMap']
        source[i] = compiled[i]['source']
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
    spans = dict((i,[]) for i in compiled)
    for name,span in sorted(set([
        (k,(pc[k][str(x)]['start'],pc[k][str(x)]['stop']))
        for k,v in compiled.items() for x,y in v.items() if not y]), key = lambda k: k[1][0]):

        if span[0]==53: continue
        print(name, span)
        d = False
        print(spans[name])
        for i in range(len(spans[name])):
            if spans[name][i][0]<=span[0]<=spans[name][i][1]:
                spans[name][i][0] = span[0]
                spans[name][i][1] = max(spans[name][i][1],span[1])
                d = True
                break
        if not d:
            spans[name].append(list(span))
    
   
    for name in compiled:
        i = 0
        while True:
            if len(spans[name])==i+1:
                break
            if spans[name][i][1] > spans[name][i+1][0]:
                spans[name][i][1] = max(spans[name][i][1], spans[name][i+1][1])
                del spans[name][i+1]
            else:
                i += 1
        for span in spans[name]:
            print(source[name][span[0]:span[1]])
        
    
    #print(results.count(0)/len(results))
    #print(spans)
    #print(pc)
    # pcMap doesn't work on constructor since it's only generated for deployed bytecode