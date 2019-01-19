from docopt import docopt
import os
import re
import shutil   

from lib.services.compiler import compile_contracts


REVERT_HOLDER = ":::COVERAGE-REVERT:::"
EVENT_HOLDER = ":::COVERAGE-EVENT:::"

__doc__ = """Usage: brownie coverage [<filename>] [options]

Arguments:
  <filename>         Only run tests from a specific file

Options:
  --help             Display this message
  --verbose          Enable verbose reporting
  --gas              Display gas profile for function calls

Coverage will modify the contracts and run your unit tests to get estimate
of how much coverage you have.  so simple..."""


def _replace(contract, span, repl):
    return (
        contract[:span[0]] +
        repl.format(revert=REVERT_HOLDER, event=EVENT_HOLDER) +
        contract[span[1]:]
    )


def _matches(contract, pattern):
    return [(
        i.span(),
        i.group().replace('{','{{').replace('}','}}')
    ) for i in list(re.finditer(pattern, contract))[::-1]]


def generate_new_contract(filename):
    contract = open(filename,'r').read()

    # remove comments /* */
    for span, match in _matches(contract, '\/\*[\s\S]*?\*\/'):
        contract = _replace(contract, span, "")

    # remove comments //
    for span, match in _matches(contract, '\/\/.*'):
        contract = _replace(contract, span, "")

    # add coverage event at start of contract
    for span, match in _matches(contract, 'contract[^{]*{'):
        contract = _replace(contract, span, match+" event Coverage(bytes4 id);")

    #reverts
    for span, match in _matches(contract, 'revert *\([^;]*(?=;)'):
        contract = _replace(contract, span, 'revert("{revert}")')

    # requires with an an error string - change the string
    for span, match in _matches(contract, 'require *\([^;]*(?=")'):
        contract = _replace(contract, span, match[:match.index('"')]+'"{revert}')

    # requires without an error string - add one
    for span, match in _matches(contract, 'require[^"]*?(?=\;)'):
        contract = _replace(contract, span, match[:-1]+',"{revert}")')

    # requires involving &&
    for span, match in _matches(contract, "require *\([^;]*&&"):
        contract = _replace(
            contract,
            span,
            match.replace('&&',',"{revert}"); require(')
        )

    # requires involving ||
    for span, match in _matches(contract, "require *\([^;]*\|\|[^;]*;"):
        new = " ".join(match.split())
        new = (
            "if " + 
            new[7:new.index(',')] + 
            ') {{ emit Coverage({event}); }} else {{ revert("{revert}"); }}'
        )
        for i in range(new.count('||')):
            new = (
                new[:new.index('||')] + 
                ') {{ emit Coverage({event}); }} else if (' +
                new[new.index('||')+2:]
            )
        contract = _replace(contract, span, new)

    # beginning of a function
    for span, match in _matches(contract, 'function[\s\S]*?{'):
        if 'view' in match or 'pure' in match:
            continue
        contract = _replace(contract, span, match+' emit Coverage({event});')

    # put brackets around if statements
    for span, match in _matches(contract, 'if *\([^{;]*?\)[^){]{1,}?;(?! *})'):
        match = (
            match[:match.rindex(')')] + 
            ') {{ ' +
            match[match.rindex(')')+1:] + 
            ' }}'
        )
        contract = _replace(contract, span, match)

    # place events on if statements that don't use ||
    for span, match in _matches(contract, 'if *\([^|;]*?\{'):
        contract = _replace(contract, span, match+" emit Coverage({event}); ")

    for span, match in _matches(contract, 'else *{'):
        contract = _replace(contract, span, match+" emit Coverage({event}); ")

    #events on if statements using ||
    for span, match in _matches(contract, 'if[^{]*?\|\|[^{]*{'):
        match = match.replace('\n','').replace('\t','')
        items = match.split('||')
        items[0]+=") {{ emit Coverage({event}); }}"
        items[-1] = "if (" + items[-1]+" emit Coverage({event}); }}"
        for i in range(1,len(items)-1):
            items[i] = "if ("+items[i]+") {{ emit Coverage({event}); }}"
        contract = _replace(contract, span, match+" ".join(items))

    open(filename,'w').write(contract)


def main():
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
        for filename in contract_files:
            generate_new_contract(filename)
        compile_contracts('.coverage')
    finally:
        #shutil.rmtree('.coverage')
        shutil.rmtree('build/contracts')
        os.rename('build/.contracts','build/contracts')

