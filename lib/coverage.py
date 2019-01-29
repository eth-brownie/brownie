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
    targets = {}
    for name in compiled:
        pc = compiled[name]['pcMap']
        targets[name] = {}
        for i in range(1,len(pc)-1):
            if not pc[i]['contract']:
                continue
            if pc[i]['contract'] not in source:
                source[pc[i]['contract']] = open(pc[i]['contract']).read()
            if pc[i]['op'] == "REVERT":
                targets[name][pc[i]['pc']] = {
                    'count':0,
                    'source': source[pc[i]['contract']][pc[i]['start']:pc[i]['stop']],
                    'msg': "revert not hit"
                }
            elif pc[i]['op'] in ("JUMP", "RETURN") and pc[i+1]['op'] == "JUMPDEST":
                if _contains(pc[i], pc[i+1]):
                    targets[name][pc[i]['pc']] = {
                        'count':0,
                        'source': source[pc[i]['contract']][pc[i]['start']:pc[i]['stop']],
                        'msg': "return not hit"
                    }
                elif not _overlap(pc[i], pc[i+1]):
                    targets[name][pc[i]['pc']] = {
                        'count':0,
                        'source': source[pc[i]['contract']][pc[i]['start']:pc[i]['stop']],
                        'msg': "final return not hit"
                    }
            elif pc[i]['op'] == "JUMPDEST" and pc[i-1]['op'] in ("JUMP", "RETURN", "REVERT"):
                if pc[i-1]['op']=="REVERT" and _same(pc[i], pc[i-1]):
                    targets[name][pc[i]['pc']] = {
                        'count':0,
                        'source': source[pc[i]['contract']][pc[i]['start']:pc[i]['stop']],
                        'msg': "did not make it past revert"
                    }
                elif not _overlap(pc[i], pc[i-1]):
                    targets[name][pc[i]['pc']] = {
                        'count':0,
                        'source': source[pc[i]['contract']][pc[i]['start']:pc[i]['stop']],
                        'msg': "function was not called"
                    }
            elif pc[i]['op'] == "JUMPI" and pc[i+1]['op']!="INVALID":
                
                try:
                    s = next(x for x in pc[i-2::-1] if x['op']!="JUMPDEST" and _contains(x, pc[i]))
                except StopIteration:
                    continue
                targets[name][pc[i]['pc']] = {
                    'count':0,
                    'source': source[s['contract']][s['start']:s['stop']],
                    'jump': True,
                    'msg': "jumpi"
                }


    for filename in test_files:
        history, tb = run_test(filename)
        if tb:
            sys.exit(
                "\n{0[error]}ERROR{0}: Cannot ".format(color) +
                "calculate coverage while tests are failing\n\n" + 
                "Exception info for {}:\n{}".format(tb[0], tb[1])
            )
        for trace in [x for i in history[1:] for x in i.trace]:
            c = targets[trace['contractName']]
            if trace['pc'] in c:
                c[trace['pc']]['count'] += 1
    print(k for k,v in targets['Token'].items() if not v['count'])

# pcMap comparisons

def _same(a, b):
    return a['start']==b['start'] and a['stop']==b['stop']

# a is fully contained by b
def _contains(a, b):
    if _same(a,b): return False
    return a['start']>=b['start'] and a['stop']<=b['stop']

# a and b overlap in any way
def _overlap(a, b):
    if a['start']<b['start']:
        return a['stop']>b['start']
    return b['stop']>a['start']