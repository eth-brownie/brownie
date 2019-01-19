import re


data = open('IssuingEntity.sol','r').read()

count = 0

def _replace(span, repl):
    global data, count
    data = data[:span[0]] + repl.format(count) + data[span[1]:]
    count += 1

def _matches(pattern):
    return [(i.span(), i.group()) for i in list(re.finditer(pattern, data))[::-1]]

#reverts
for span, match in _matches('revert {0,}\([^;]*(?=;)'):
    _replace(span, 'revert("ERROR{}")');


# requires with an an error string - change the string
for span, match in _matches('require {0,}\([^;]*(?=")'):
    _replace(span, match[:match.index('"')]+'"ERROR{}')

# requires without an error string - add one
for span, match in _matches('require[^)"]*(?=\);)'):
    _replace(span, match+',"ERROR{}"')

# requires involving an &&
for span, match in _matches("require.*&&"):
    _replace(span, match.replace('&&',',"ERROR{}"); require('))

print(data)