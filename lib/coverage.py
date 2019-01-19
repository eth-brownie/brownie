from docopt import docopt
import os
import re
import shutil   

if os.path.exists('.coverage'):
    shutil.rmtree('.coverage')

shutil.copytree('contracts', '.coverage')

data = open('IssuingEntity.sol','r').read()

revert = ":::COVERAGE-REVERT:::"
event = "0x00"

def _replace(span, repl):
    global data
    data = data[:span[0]] + repl.format(revert=revert, event=event) + data[span[1]:]

def _matches(pattern):
    return [(
        i.span(),
        i.group().replace('{','{{').replace('}','}}')
    ) for i in list(re.finditer(pattern, data))[::-1]]

# remove comments
for span, match in _matches('\/\*[\s\S]*?\*\/'):
    _replace(span, "")

# remove more comments
for span, match in _matches('\/\/.*'):
    _replace(span, "")

# add coverage event
for span, match in _matches('contract[^{]*{'):
    _replace(span, match+" event Coverage(bytes4 id);")

#reverts
for span, match in _matches('revert *\([^;]*(?=;)'):
    _replace(span, 'revert("{revert}")')


# requires with an an error string - change the string
for span, match in _matches('require *\([^;]*(?=")'):
    _replace(span, match[:match.index('"')]+'"{revert}')

# requires without an error string - add one
for span, match in _matches('require[^"]*?(?=\;)'):
    _replace(span, match[:-1]+',"{revert}")')

# requires involving &&
for span, match in _matches("require *\([^;]*&&"):
    _replace(span, match.replace('&&',',"{revert}"); require('))

# requires involving ||
for span, match in _matches("require *\([^;]*\|\|[^;]*;"):
    new = " ".join(match.split())
    new = "if "+new[7:new.index(',')]+') {{ emit Coverage({event}); }} else {{ revert("{revert}"); }}'
    for i in range(new.count('||')):
        new = new[:new.index('||')]+') {{ emit Coverage({event}); }} else if ('+ new[new.index('||')+2:]
    _replace(span, new)

# beginning of a function
for span, match in _matches('function[\s\S]*?{'):
    if 'view' in match or 'pure' in match:
        continue
    #match = match.replace('{','{{').replace('}','}}')
    _replace(span, match+' emit Coverage({event});')

# put brackets around if statements
for span, match in _matches('if *\([^{;]*?\)[^){]{1,}?;(?! *})'):
    match = match[:match.rindex(')')]+') {{ '+ match[match.rindex(')')+1:] + ' }}'
    _replace(span, match)

# place events on if statements that don't use ||
for span, match in _matches('if *\([^|;]*?\{'):
    #match = match.replace('{','{{').replace('}','}}')
    _replace(span, match+" emit Coverage({event}); ")

for span, match in _matches('else *{'):
    #match = match.replace('{','{{').replace('}','}}')
    _replace(span, match+" emit Coverage({event}); ")


#events on if statements using ||
for span, match in _matches('if[^{]*?\|\|[^{]*{'):
    match = match.replace('\n','').replace('\t','')
    items = match.split('||')
    items[0]+=") {{ emit Coverage({event}); }}"
    items[-1] = "if (" + items[-1]+" emit Coverage({event}); }}"
    for i in range(1,len(items)-1):
        items[i] = "if ("+items[i]+") {{ emit Coverage({event}); }}"
    _replace(span, match+" ".join(items))


print(data)