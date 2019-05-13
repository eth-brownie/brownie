#!/usr/bin/python3

import json
from pathlib import Path
import re

from brownie.project import Build, Sources

build = Build()
sources = Sources()


def analyze_coverage(history):
    '''Given a list of TransactionReceipt objects, analyzes test coverage and
    returns a coverage evaluation dict.
    '''
    coverage_eval = {}
    coverage_map = {}
    pcMap = {}
    for tx in history:
        if not tx.receiver:
            continue
        tx_eval = {}
        for i in range(len(tx.trace)):
            t = tx.trace[i]
            pc = t['pc']
            name = t['contractName']
            path = t['source']['filename']
            if not name or not path or name not in build:
                continue

            # prevent repeated requests to build object
            if name not in pcMap:
                pcMap[name] = build[name]['pcMap']
                coverage_map[name] = build[name]['coverageMap']
                coverage_eval[name] = dict((i, {}) for i in coverage_map[name])
            if name not in tx_eval:
                tx_eval[name] = dict((i, {}) for i in coverage_map[name])

            fn = pcMap[name][pc]['fn']
            if not fn:
                continue

            coverage_eval[name][path].setdefault(fn, {'tx': set(), 'true': set(), 'false': set()})
            tx_eval[name][path].setdefault(fn, set())
            if t['op'] != "JUMPI":
                if 'coverageIndex' not in pcMap[name][pc]:
                    continue
                # if not a JUMPI, record at the coverage map index
                idx = pcMap[name][pc]['coverageIndex']
                if coverage_map[name][path][fn][idx]['jump']:
                    tx_eval[name][path][fn].add(pcMap[name][pc]['coverageIndex'])
                else:
                    coverage_eval[name][path][fn]['tx'].add(pcMap[name][pc]['coverageIndex'])
                continue
            # if a JUMPI, check that we hit the jump AND the related coverage map
            try:
                idx = coverage_map[name][path][fn].index(
                    next(i for i in coverage_map[name][path][fn] if i['jump'] == pc)
                )
            except StopIteration:
                continue
            if idx not in tx_eval[name][path][fn] or idx in coverage_eval[name][path][fn]['tx']:
                continue
            key = ('false', 'true') if tx.trace[i+1]['pc'] == pc+1 else ('true', 'false')
            # if the conditional evaluated both ways, record on the main eval dict
            if idx not in coverage_eval[name][path][fn][key[1]]:
                coverage_eval[name][path][fn][key[0]].add(idx)
                continue
            coverage_eval[name][path][fn][key[1]].discard(idx)
            coverage_eval[name][path][fn]['tx'].add(idx)
    return _calculate_pct(coverage_eval)


def merge_coverage_eval(*coverage_eval):
    '''Given a list of coverage evaluation dicts, returns an aggregated evaluation dict.'''
    merged_eval = coverage_eval[0]
    for coverage in coverage_eval[1:]:
        for contract_name in list(coverage):
            del coverage[contract_name]['pct']
            if contract_name not in merged_eval:
                merged_eval[contract_name] = coverage.pop(contract_name)
                continue
            for source, fn_name in [(k, x) for k, v in coverage[contract_name].items() for x in v]:
                f = merged_eval[contract_name][source][fn_name]
                c = coverage[contract_name][source][fn_name]
                if not f['pct']:
                    f.update(c)
                    continue
                if not c['pct'] or f == c:
                    continue
                if f['pct'] == 1 or c['pct'] == 1:
                    merged_eval[contract_name][source][fn_name] = {'pct': 1}
                    continue
                f['true'] += c['true']
                f['false'] += c['false']
                f['tx'] = list(set(f['tx']+c['tx']+[i for i in f['true'] if i in f['false']]))
                f['true'] = list(set([i for i in f['true'] if i not in f['tx']]))
                f['false'] = list(set([i for i in f['false'] if i not in f['tx']]))
    return _calculate_pct(merged_eval)


def merge_coverage_files(coverage_files):
    '''Given a list of coverage evaluation file paths, returns an aggregated evaluation dict.'''
    coverage_eval = []
    for filename in coverage_files:
        path = Path(filename)
        if not path.exists():
            continue
        coverage_eval.append(json.load(path.open())['coverage'])
    return merge_coverage_eval(*coverage_eval)


def _calculate_pct(coverage_eval):
    '''Internal method to calculate coverage percentages'''
    for name in coverage_eval:
        contract_count = 0
        coverage_map = build[name]['coverageMap']
        for path, fn_name in [(k, x) for k, v in coverage_map.items() for x in v]:
            result = coverage_eval[name][path]
            if fn_name not in result:
                result[fn_name] = {'pct': 0}
                continue
            if 'pct' in result[fn_name] and result[fn_name]['pct'] in (0, 1):
                if result[fn_name]['pct']:
                    contract_count += build[name]['coverageMapTotals'][fn_name]
                result[fn_name] = {'pct': result[fn_name]['pct']}
                continue
            result = dict((k, list(v) if type(v) is set else v) for k, v in result[fn_name].items())
            coverage_eval[name][path][fn_name] = result
            count = 0
            maps = coverage_map[path][fn_name]
            for idx, item in enumerate(maps):
                if idx in result['tx']:
                    count += 2 if item['jump'] else 1
                    continue
                if not item['jump']:
                    continue
                if idx in result['true'] or idx in result['false']:
                    count += 1
            contract_count += count
            result['pct'] = round(count / build[name]['coverageMapTotals'][fn_name], 4)
            if result['pct'] == 1:
                coverage_eval[name][path][fn_name] = {'pct': 1}
        pct = round(contract_count / build[name]['coverageMapTotals']['total'], 4)
        coverage_eval[name]['pct'] = pct
    return coverage_eval


def generate_report(coverage_eval):
    '''Converts coverage evaluation into highlight data suitable for the GUI'''
    report = {
        'highlights': {},
        'coverage': {},
        'sha1': {}
    }
    for name, coverage in coverage_eval.items():
        report['highlights'][name] = {}
        report['coverage'][name] = {'pct': coverage['pct']}
        for path in [i for i in coverage if i != "pct"]:
            coverage_map = build[name]['coverageMap'][path]
            report['highlights'][name][path] = []
            for fn_name, lines in coverage_map.items():
                # if function has 0% or 100% coverage, highlight entire function
                report['coverage'][name][fn_name] = coverage[path][fn_name]['pct']
                if coverage[path][fn_name]['pct'] in (0, 1):
                    color = "green" if coverage[path][fn_name]['pct'] else "red"
                    start, stop = sources.get_fn_offset(path, fn_name)
                    report['highlights'][name][path].append(
                        (start, stop, color, "")
                    )
                    continue
                # otherwise, highlight individual statements
                for i, ln in enumerate(lines):
                    if i in coverage[path][fn_name]['tx']:
                        color = "green"
                    elif i in coverage[path][fn_name]['true']:
                        color = "yellow" if _evaluate_branch(path, ln) else "orange"
                    elif i in coverage[path][fn_name]['false']:
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
    except Exception:
        return False

    # remove comments, strip whitespace
    before = source[idx:start]
    for pattern in (r'\/\*[\s\S]*?\*\/', r'\/\/[^\n]*'):
        for i in re.findall(pattern, before):
            before = before.replace(i, "")
    before = before.strip("\n\t (")

    idx = source[stop:].index(';')+len(source[:stop])
    if idx <= stop:
        return False
    after = source[stop:idx].split()
    after = next((i for i in after if i != ")"), after[0])[0]
    if (
        (before[-2:] == "if" and after == "|") or
        (before[:7] == "require" and after in (")", "|", ","))
    ):
        return True
    return False


def _maxindex(source):
    comp = [i for i in [";", "}", "{"] if i in source]
    return max([source.rindex(i) for i in comp])+1
