from docopt import docopt
import os
import re
import shutil   
import sys

from lib.test import run_test
from lib.services import color
from lib.services.compiler import compile_contracts


HOLDER = ":::COVERAGE:::"

__doc__ = """Usage: brownie coverage [<filename>] [options]

Arguments:
  <filename>         Only run tests from a specific file

Options:
  --help             Display this message
  --verbose          Enable verbose reporting

Coverage will modify the contracts and run your unit tests to get estimate
of how much coverage you have.  so simple..."""

count = -1
coverage_index={}

def _replace(contract, span, repl):
    global count
    count += 1
    repl = repl.format(holder="0x{:0>8}".format(hex(count)[2:]))
    return (
        contract[:span[0]] + repl + contract[span[1]:],
        len(repl) - (span[1]-span[0])
    ) 


def _matches(contract, pattern):
    return [(
        i.span(),
        i.group().replace('{','{{').replace('}','}}')
    ) for i in list(re.finditer(pattern, contract))[::-1]]


def generate_new_contract(filename):#, count):
    contract = open(filename,'r').read()
    offset = {}

    # remove comments /* */
    for span, match in _matches(contract, '\/\*[\s\S]*?\*\/'):
        contract, offset[span[1]] = _replace(contract, span, "")

    # remove comments //
    for span, match in _matches(contract, '\/\/.*'):
        contract, offset[span[1]] = _replace(contract, span, "")

    # add coverage event at start of contract
    for span, match in _matches(contract, '(contract|library)[^{]*{'):
        contract, offset[span[1]] = _replace(contract, span, match+" event Coverage(bytes4 id);")

    # remove view/pure
    for span, match in _matches(contract, 'function[^{]*?(view|pure)'):
        contract, offset[span[1]] = _replace(contract, span, match[:-4])
    
    # returns
    for span, match in _matches(contract, 'return '):
        o = sum(offset[i] for i in sorted(offset) if i<span[0])
        coverage_index[count+1] = (
            filename,
            span[0] - o,
            span[1] - o
        )
        contract, offset[span[1]] = _replace(contract, span, 'emit Coverage({holder}); return ')
        

    # reverts
    for span, match in _matches(contract, 'revert *\([^;]*(?=;)'):
        o = sum(offset[i] for i in sorted(offset) if i<span[0])
        coverage_index[count+1] = (
            filename,
            span[0] - o,
            span[1] - o
        )
        contract, offset[span[1]] = _replace(contract, span, 'revert("{holder}")')

    # requires with an an error string - change the string
    for span, match in _matches(contract, 'require *\([^;]*(?=")'):
        o = sum(offset[i] for i in sorted(offset) if i<span[0])
        coverage_index[count+1] = (
            filename,
            span[0] - o,
            span[1] - o
        )
        contract, offset[span[1]] = _replace(contract, span, match[:match.index('"')]+'"{holder}')

    # requires without an error string - add one
    for span, match in _matches(contract, 'require[^"]*?(?=\;)'):
        o = sum(offset[i] for i in sorted(offset) if i<span[0])
        coverage_index[count+1] = (
            filename,
            span[0] - o,
            span[1] - o
        )
        contract, offset[span[1]] = _replace(contract, span, match[:-1]+',"{holder}")')

    # requires involving &&
    for span, match in _matches(contract, "require *\([^;]*&&"):
        contract, offset[span[1]] = _replace(
            contract,
            span,
            match.replace('&&',',"{holder}"); require(')
        )

    # requires involving ||
    for span, match in _matches(contract, "require *\([^;]*\|\|[^;]*;"):
        new = " ".join(match.split())
        new = (
            "if " + 
            new[7:new.index(',')] + 
            ') {{ emit Coverage({holder}); }} else {{ revert("{holder}"); }}'
        )
        for i in range(new.count('||')):
            new = (
                new[:new.index('||')] + 
                ') {{ emit Coverage({holder}); }} else if (' +
                new[new.index('||')+2:]
            )
        contract, offset[span[1]] = _replace(contract, span, new)

    # beginning of a function
    for span, match in _matches(contract, 'function[\s\S]*?{'):
        if 'view' in match or 'pure' in match:
            print(match)
            continue
        contract, offset[span[1]] = _replace(contract, span, match+' emit Coverage({holder});')

    # put brackets around if statements
    for span, match in _matches(contract, 'if *\([^{;]*?\)[^){]{1,}?;(?! *})'):
        match = (
            match[:match.rindex(')')] + 
            ') {{ ' +
            match[match.rindex(')')+1:] + 
            ' }}'
        )
        contract, offset[span[1]] = _replace(contract, span, match)

    # place events on if statements that don't use ||
    for span, match in _matches(contract, 'if *\([^|;]*?\{'):
        contract, offset[span[1]] = _replace(contract, span, match+" emit Coverage({holder}); ")

    for span, match in _matches(contract, 'else *{'):
        contract, offset[span[1]] = _replace(contract, span, match+" emit Coverage({holder}); ")

    #events on if statements using ||
    for span, match in _matches(contract, 'if[^{]*?\|\|[^{]*{'):
        match = match.replace('\n','').replace('\t','')
        items = match.split('||')
        items[0]+=") {{ emit Coverage({holder}); }}"
        items[-1] = "if (" + items[-1]+" emit Coverage({holder}); }}"
        for i in range(1,len(items)-1):
            items[i] = "if ("+items[i]+") {{ emit Coverage({holder}); }}"
        contract, offset[span[1]] = _replace(contract, span, match+" ".join(items))

    #while contract.count(HOLDER):
    #    count += 1
    #    contract = contract.replace(HOLDER,"0x{:0>8}".format(hex(count)[2:]), 1)

    open(filename,'w').write(contract)
    #return count


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
    
    if os.path.exists('.coverage'):
        shutil.rmtree('.coverage')

    if not os.path.exists('.coverage'):
        shutil.copytree('contracts', '.coverage')

    os.rename('build/contracts','build/.contracts')
    os.mkdir('build/contracts')

    contract_files = [
        "{}/{}".format(i[0], x) for i in os.walk('.coverage') for x in i[2]
    ]

    try:
        #count = -1
        for filename in contract_files:
            generate_new_contract(filename)#, count)
        results = dict((i,0) for i in range(count))
        o = open('contracts/Token.sol','r').read()
        for i in coverage_index.values():
            if "Token" not in i[0]: continue
            print(o[i[1]:i[2]])
        #print(coverage_index)
        compile_contracts('.coverage')
        for filename in test_files:
            history, tb = run_test(filename)
            if tb:
                sys.exit(
                    "\n{0[bright red]}ERROR{0}: Cannot ".format(color) +
                    "calculate coverage while tests are failing\n\n" + 
                    "Exception info for {}:\n{}".format(tb[0], tb[1])
                )
            for event in [x for i in history for x in i.events if x['name']=="Coverage"]:
                results[int(event['data'][0]['value'], 16)] += 1
        pct = list(results.values()).count(0)/len(results)
        print("\nTest coverage is currently at {0[bright cyan]}{1:.1%}{0}".format(color,pct))

    finally:
        #shutil.rmtree('.coverage')
        shutil.rmtree('build/contracts')
        os.rename('build/.contracts','build/contracts')

