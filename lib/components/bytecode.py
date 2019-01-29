#!/usr/bin/python3


class Source:

    def __init__(self):
        self._s = {}
    
    def __call__(self, op):
        path = op['contract']
        if path not in self._s:
            self._s[path] = open(path).read()
        return self._s[path][op['start']:op['stop']]

def isolate_functions(compiled):
    pcMap = compiled['pcMap']
    fn_map = {}
    source = Source()
    for op in _oplist(pcMap, "JUMPDEST"):
        s = source(op)
        if s[:8] in ("contract", "library ", "interfac"):
            continue
        if s[:8]=="function":
            fn = s[9:s.index('(')]
        elif " public " in s:
            fn = s[s.index(" public ")+8:].split(' =')[0]
        else:
            continue
        if fn not in fn_map:
            fn_map[fn] = _base(op)
            fn_map[fn]['name']=fn
        fn_map[fn]['pc'].add(op['pc'])
    
    fn_map = _sort(fn_map.values())
    if not fn_map:
        return []
    for op in _oplist(pcMap):
        try:
            f = _next(fn_map, op)
        except StopIteration:
            continue
        if op['stop']>f['stop']:
            continue
        f['pc'].add(op['pc'])
    return fn_map

def isolate_lines(compiled):
    pcMap = compiled['pcMap']
    line_map = {}
    source = Source()
    
    for i in [pcMap.index(i) for i in _oplist(pcMap, "JUMPI")]:
        op = pcMap[i]
        if op['contract'] not in line_map:
            line_map[op['contract']] = []
        if pcMap[i+1]['op'] == "INVALID" or " public " in source(op):
            continue
        try:
            req = next(
                x for x in pcMap[i-2::-1] if
                x['contract'] and 
                x['op']!="JUMPDEST" and
                x['start']+x['stop']!=op['start']+op['stop']
            )
        except StopIteration:
            continue
        line_map[op['contract']].append(_base(req))
        line_map[op['contract']][-1].update({
            'jump':op['pc'], 'true': set(), 'false': set()
        })
    for op in _oplist(pcMap):
        if ';' in source(op):
            continue
        if op['contract'] not in line_map:
            line_map[op['contract']] = []
        try:
            ln = _next(line_map[op['contract']], op)
        except StopIteration:
            line_map[op['contract']].append(_base(op))
            continue
        if op['stop'] > ln['stop']:
            if ln['jump']:
                continue
            ln['stop'] = op['stop']
        ln['pc'].add(op['pc'])
        i = 0
        line_map[op['contract']] = _sort(line_map[op['contract']])
        ln_map = line_map[op['contract']]
        while True:
            if len(ln_map)<=i+1:
                break
            if not (ln_map[i]['jump'] or ln_map[i+1]['jump']):
                if ln_map[i]['stop'] >= ln_map[i+1]['start']:
                    ln_map[i]['pc'] |= ln_map[i+1]['pc']
                    del ln_map[i+1]
                    continue
            i+=1
    return [x for v in line_map.values() for x in v]

def get_coverage_map(compiled):
    fn_map = {}
    line_map = {}
    for contract in compiled:
        fn_map[contract] = isolate_functions(compiled[contract])
        line_map[contract] = isolate_lines(compiled[contract])
        for fn in fn_map[contract]:
            for ln in [
                i for i in line_map[contract] if
                i['contract']==fn['contract'] and
                i['start']==fn['start'] and i['stop']==fn['stop']
            ]:
                line_map[contract].remove(ln)
            for ln in [
                i for i in line_map[contract] if
                i['contract']==fn['contract'] and
                i['start']>=fn['start'] and i['stop']<=fn['stop']
            ]:
                ln['name'] = fn['name']
    return fn_map, line_map


def _next(list_, op):
    return next(
        i for i in list_ if i['contract']==op['contract'] and
        i['start']<=op['start']<i['stop']
    )

def _sort(list_):
    return sorted(list_, key = lambda k: (k['contract'],k['start'],k['stop']))

def _oplist(pcMap, op=None):
    return [i for i in pcMap if i['contract'] and (not op or op==i['op'])]

def _base(op):
    return {
        'name': None,
        'start':op['start'],
        'stop': op['stop'],
        'pc':set([op['pc']]),
        'contract':op['contract'],
        'jump': False,
        'tx':set()
    }