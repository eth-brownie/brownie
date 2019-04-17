#!/usr/bin/python3

class Source:

    def __init__(self):
        self._s = {}
    
    def __call__(self, op):
        path = op['contract']
        if path not in self._s:
            self._s[path] = open(path, encoding="utf-8").read()
        return self._s[path][op['start']:op['stop']]


def get_coverage_map(build):
    """Given the compiled project as supplied by compiler.compile_contracts(),
    returns the function and line based coverage maps for unit test coverage
    evaluation.

    A coverage map item is structured as follows:

    {
        
        "/path/to/contract/file.sol":{
            "functionName":{
                "fn": {},
                "line":[{},{},{}]
            }
        }
    }

    Each dict in fn/line is as follows:

    {
        'start': source code start offset 
        'stop': source code stop offset
        'pc': set of opcode program counters tied to the map item
        'jump': pc of the JUMPI instruction, if it is a jump
        'tx': empty set, used to record transactions that hit the item
    }

    Items relating to jumps also include keys 'true' and 'false', which are
    also empty sets used in the same way as 'tx'"""

    fn_map = dict((x,{}) for x in build['allSourcePaths'])

    for i in _isolate_functions(build):
        fn_map[i.pop('contract')][i.pop('method')] = {'fn':i,'line':[]}
    line_map = _isolate_lines(build)
    if not line_map:
        return {}

    # future me - i'm sorry for this line
    for source, fn_name, fn in [(k,x,v[x]['fn']) for k,v in fn_map.items() for x in v]:
        for ln in [
            i for i in line_map if
            i['contract']==source and
            i['start']==fn['start'] and i['stop']==fn['stop']
        ]:
            # remove duplicate mappings
            line_map.remove(ln)
        for ln in [
            i for i in line_map if
            i['contract']==source and
            i['start']>=fn['start'] and i['stop']<=fn['stop']
        ]:
            # apply method names to line mappings
            line_map.remove(ln)
            fn_map[ln.pop('contract')][fn_name]['line'].append(ln)
        fn_map[source][fn_name]['total'] = sum([1 if not i['jump'] else 2 for i in fn_map[source][fn_name]['line']])
    return fn_map


def _isolate_functions(compiled):
    '''Identify function level coverage map items.'''
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
            fn = s[s.index(" public ")+8:].split(' =')[0].strip()
        else:
            continue
        if fn not in fn_map:
            fn_map[fn] = _base(op)
            fn_map[fn]['method']=fn
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


def _isolate_lines(compiled):
    '''Identify line based coverage map items.

    For lines where a JUMPI is not present, coverage items will merge
    to include as much of the line as possible in a single item. Where a
    JUMPI is involved, no merge will happen and overlapping non-jump items
    are discarded.'''
    pcMap = compiled['pcMap']
    line_map = {}
    source = Source()

    # find all the JUMPI opcodes
    for i in [pcMap.index(i) for i in _oplist(pcMap, "JUMPI")]:
        op = pcMap[i]
        if op['contract'] not in line_map:
            line_map[op['contract']] = []
        # if followed by INVALID or the source contains public, ignore it
        if pcMap[i+1]['op'] == "INVALID" or " public " in source(op):
            continue
        try:
            # JUMPI is to the closest previous opcode that has
            # a different source offset and is not a JUMPDEST
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
            'jump':op['pc'],# 'true': set(), 'false': set()
        })

    # analyze all the opcodes
    for op in _oplist(pcMap):
        # ignore code that spans multiple lines
        if ';' in source(op):
            continue
        if op['contract'] not in line_map:
            line_map[op['contract']] = []
        # find existing related coverage map item, make a new one if none exists
        try:
            ln = _next(line_map[op['contract']], op)
        except StopIteration:
            line_map[op['contract']].append(_base(op))
            continue
        if op['stop'] > ln['stop']:
            # if coverage map item is a jump, do not modify the source offsets
            if ln['jump']:
                continue
            ln['stop'] = op['stop']
        ln['pc'].add(op['pc'])

    # sort the coverage map and merge overlaps where possible
    for contract in line_map:
        line_map[contract] = _sort(line_map[contract])
        ln_map = line_map[contract]
        i = 0
        while True:
            if len(ln_map)<=i+1:
                break
            if ln_map[i]['jump']:
                i+=1
                continue
            # JUMPI overlaps cannot merge
            if ln_map[i+1]['jump']:
                if ln_map[i]['stop']>ln_map[i+1]['start']:
                    del ln_map[i]
                else:
                    i+=1
                continue
            if ln_map[i]['stop'] >= ln_map[i+1]['start']:
                ln_map[i]['pc'] |= ln_map[i+1]['pc']
                ln_map[i]['stop'] = max(ln_map[i]['stop'], ln_map[i+1]['stop'])
                del ln_map[i+1]
                continue
            i+=1
    return [x for v in line_map.values() for x in v]


def _next(coverage_map, op):
    '''Given a coverage map and an item from pcMap, returns the related
    coverage map item (based on source offset overlap).'''
    return next(
        i for i in coverage_map if i['contract']==op['contract'] and
        i['start']<=op['start']<i['stop']
    )


def _sort(list_):
    return sorted(list_, key = lambda k: (k['contract'],k['start'],k['stop']))


def _oplist(pcMap, op=None):
    return [i for i in pcMap if i['contract'] and (not op or op==i['op'])]


def _base(op):
    return {
        'contract':op['contract'],
        'start':op['start'],
        'stop': op['stop'],
        'pc':set([op['pc']]),
        'jump': False,
#        'tx':set()
    }