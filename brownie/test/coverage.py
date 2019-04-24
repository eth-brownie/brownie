#!/usr/bin/python3

import json
from pathlib import Path

from brownie.project import build


def merge_coverage(coverage_files):
    final = {}
    for filename in coverage_files:
        path = Path(filename)
        if not path.exists():
            continue
        coverage = json.load(path.open())['coverage']
        for key in list(coverage):
            if key not in final:
                final[key] = coverage.pop(key)
                continue
            for source, fn_name in [(k, x) for k, v in coverage[key].items() for x in v]:
                f = final[key][source][fn_name]
                c = coverage[key][source][fn_name]
                if not c['pct']:
                    continue
                if f['pct'] == 1 or c['pct'] == 1:
                    final[key][source][fn_name] = {'pct': 1}
                    continue
                _list_to_set(f,'line').update(c['line'])
                if 'true' in c:
                    _list_to_set(f, "true").update(c['true'])
                    _list_to_set(f, "false").update(c['false'])
                for i in f['true'].intersection(f['false']):
                    f['line'].add(i)
                    f['true'].discard(i)
                    f['false'].discard(i)
    return final


def _list_to_set(obj, key):
    if key in obj:
        obj[key] = set(obj[key])
    else:
        obj[key] = set()
    return obj[key]


def analyze_coverage(history):
    coverage_map = {}
    coverage_eval = {}
    for tx in history:
        if not tx.receiver:
            continue
        for i in range(len(tx.trace)):
            t = tx.trace[i]
            pc = t['pc']
            name = t['contractName']
            source = t['source']['filename']
            if not name or not source:
                continue
            if name not in coverage_map:
                coverage_map[name] = build.get_contract(name)['coverageMap']
                coverage_eval[name] = dict((i, {}) for i in coverage_map[name])
            try:
                # find the function map item and record the tx
                fn = next(v for k, v in coverage_map[name][source].items() if pc in v['fn']['pc'])
                fn['fn'].setdefault('tx',set()).add(tx)
                if t['op'] != "JUMPI":
                    # if not a JUMPI, find the line map item and record
                    ln = next(i for i in fn['line'] if pc in i['pc'])
                    for key in ('tx', 'true', 'false'):
                        ln.setdefault(key, set())
                    ln['tx'].add(tx)
                    continue
                # if a JUMPI, we need to have hit the jump pc AND a related opcode
                ln = next(i for i in fn['line'] if pc == i['jump'])
                for key in ('tx', 'true', 'false'):
                    ln.setdefault(key, set())
                if tx not in ln['tx']:
                    continue
                # if the next opcode is not pc+1, the JUMPI was executed truthy
                key = 'false' if tx.trace[i+1]['pc'] == pc+1 else 'true'
                ln[key].add(tx)
            # pc didn't exist in map
            except StopIteration:
                continue

    for contract, source, fn_name, maps in [(k,w,y,z) for k,v in coverage_map.items() for w,x in v.items() for y,z in x.items()]:
        fn = maps['fn']
        if 'tx' not in fn or not fn['tx']:
            coverage_eval[contract][source][fn_name] = {'pct':0}
            continue
        for ln in maps['line']:
            if 'tx' not in ln:
                ln['count'] = 0
                continue
            if ln['jump']:
                ln['jump'] = [len(ln['true']), len(ln['false'])]
            ln['count'] = len(ln['tx'])
        if not [i for i in maps['line'] if i['count']]:
            coverage_eval[contract][source][fn_name] = {'pct':0}
            continue

        count = 0
        coverage = {
            'line': set(),
            'true': set(),
            'false': set()
        }
        for c,i in enumerate(maps['line']):
            if not i['count']:
                continue
            if not i['jump'] or False not in i['jump']:
                coverage['line'].add(c)
                count += 2 if i['jump'] else 1
                continue
            if i['jump'][0]:
                coverage['true'].add(c)
                count += 1
            if i['jump'][1]:
                coverage['false'].add(c)
                count += 1
        if count == maps['total']:
            coverage_eval[contract][source][fn_name] = {'pct': 1}
        else:
            coverage['pct'] = round(count/maps['total'], 4)
            coverage_eval[contract][source][fn_name] = coverage

    return coverage_eval
