#!/usr/bin/python3

import json
from pathlib import Path
import re

from brownie.project import Build, Sources

build = Build()
sources = Sources()

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
                coverage_map[name] = build[name]['coverageMap']
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


def merge_coverage(coverage_files):
    coverage_eval = {}
    for filename in coverage_files:
        path = Path(filename)
        if not path.exists():
            continue
        coverage = json.load(path.open())['coverage']
        for key in list(coverage):
            if key not in coverage_eval:
                coverage_eval[key] = coverage.pop(key)
                continue
            for source, fn_name in [(k, x) for k, v in coverage[key].items() for x in v]:
                f = coverage_eval[key][source][fn_name]
                c = coverage[key][source][fn_name]
                if not c['pct']:
                    continue
                if f['pct'] == 1 or c['pct'] == 1:
                    coverage_eval[key][source][fn_name] = {'pct': 1}
                    continue
                _list_to_set(f,'line').update(c['line'])
                if 'true' in c:
                    _list_to_set(f, "true").update(c['true'])
                    _list_to_set(f, "false").update(c['false'])
                for i in f['true'].intersection(f['false']):
                    f['line'].add(i)
                    f['true'].discard(i)
                    f['false'].discard(i)
    return coverage_eval


def _list_to_set(obj, key):
    if key in obj:
        obj[key] = set(obj[key])
    else:
        obj[key] = set()
    return obj[key]


def generate_report(coverage_eval):
    report = {
        'highlights':{},
        'sha1':{}
    }
    for name, coverage in coverage_eval.items():
        report['highlights'][name] = {}
        for path in coverage:
            coverage_map = build[name]['coverageMap'][path]
            report['highlights'][name][path] = []
            for key, fn, lines in [(k,v['fn'],v['line']) for k,v in coverage_map.items()]:
                if coverage[path][key]['pct'] in (0, 1):
                    color = "green" if coverage[path][key]['pct'] else "red"
                    report['highlights'][name][path].append(
                        (fn['start'], fn['stop'], color, "")
                    )
                    continue
                for i, ln in enumerate(lines):
                    if i in coverage[path][key]['line']:
                        color = "green"
                    elif i in coverage[path][key]['true']:
                        color = "yellow" if _evaluate_branch(path, ln) else "orange"
                    elif i in coverage[path][key]['false']:
                        color = "orange" if _evaluate_branch(path, ln) else "yellow"
                    else:
                        color = "red"
                    report['highlights'][name][path].append(
                        (ln['start'], ln['stop'], color, "")
                    )
    return report


def _evaluate_branch(path, ln):
    source = sources[path]
    start, stop = ln['start'], ln['stop']
    try:
        idx = _maxindex(source[:start])
    except:
        return False

    # remove comments, strip whitespace
    before = source[idx:start]
    for pattern in ('\/\*[\s\S]*?\*\/', '\/\/[^\n]*'):
        for i in re.findall(pattern, before):
            before = before.replace(i, "")
    before = before.strip("\n\t (")

    idx = source[stop:].index(';')+len(source[:stop])
    if idx <= stop:
        return False
    after = source[stop:idx].split()
    after = next((i for i in after if i!=")"),after[0])[0]
    if (
        (before[-2:] == "if" and after=="|") or
        (before[:7] == "require" and after in (")","|"))
    ):
        return True
    return False


def _maxindex(source):
    comp = [i for i in [";", "}", "{"] if i in source]
    return max([source.rindex(i) for i in comp])+1