#!/usr/bin/python3

from copy import deepcopy
import json
from pathlib import Path

from brownie.project import build


def analyze_coverage(history, coverage_eval={}):
    '''Given a list of TransactionReceipt objects, analyzes test coverage and
    returns a coverage evaluation dict.
    '''
    for tx in filter(lambda k: k.trace, history):
        build_json = build.get(tx.trace[0]['contractName'])
        coverage_eval = _set_coverage_defaults(build_json, coverage_eval)
        tx_trace = tx.trace
        for i in filter(lambda k: tx_trace[k]['source'], range(len(tx_trace))):
            trace = tx.trace[i]
            name = trace['contractName']
            if not build.contains(name):
                continue
            if build_json['contractName'] != name:
                build_json = build.get(name)
                coverage_eval = _set_coverage_defaults(build_json, coverage_eval)
            pc = build_json['pcMap'][trace['pc']]
            if 'statement' in pc:
                coverage_eval[name]['statements'][pc['path']].add(pc['statement'])
            if 'branch' in pc:
                key = "false" if tx.trace[i+1]['pc'] == trace['pc']+1 else "true"
                coverage_eval[name]['branches'][key][pc['path']].add(pc['branch'])
    return coverage_eval


def _set_coverage_defaults(build_json, coverage_eval):
    name = build_json['contractName']
    if name in coverage_eval:
        return coverage_eval
    coverage_eval[name] = {
        'statements': dict((k, set()) for k in build_json['coverageMap']['statements'].keys()),
        'branches': {
            "true": dict((k, set()) for k in build_json['coverageMap']['branches'].keys()),
            "false": dict((k, set()) for k in build_json['coverageMap']['branches'].keys())
        }
    }
    return coverage_eval


# REMOVE ME DURING cli/test REFACTOR, thx
def merge_files(coverage_files):
    '''Merges multiple coverage evaluation dicts that have been saved to json.'''
    coverage_eval = [json.load(Path(i).open()) for i in coverage_files]
    return merge(coverage_eval)


def merge(*coverage_eval):
    '''Merges multiple coverage evaluation dicts.'''
    merged_eval = deepcopy(coverage_eval[0])
    for cov in coverage_eval[1:]:
        for name in cov:
            if name not in merged_eval:
                merged_eval[name] = cov[name]
                continue
            _merge(merged_eval[name]['statements'], cov[name]['statements'])
            _merge(merged_eval[name]['branches']['true'], cov[name]['branches']['true'])
            _merge(merged_eval[name]['branches']['false'], cov[name]['branches']['false'])
    return merged_eval


def _merge(original, new):
    for path, map_ in new.items():
        if path not in original:
            original[path] = map_
            continue
        original[path] = set(original[path]).union(map_)


def split_by_fn(coverage_eval):
    '''Splits a coverage eval dict by contract function.
    Once this is done, the dict can no longer be merged.'''
    results = dict((i, {
        'statements': {},
        'branches': {'true': {}, 'false': {}}}
    ) for i in coverage_eval)
    for name in coverage_eval:
        coverage_map = build.get(name)['coverageMap']
        results[name]['statements'] = _split_path(
            coverage_eval[name]['statements'],
            coverage_map['statements']
        )
        for key in ('true', 'false'):
            results[name]['branches'][key] = _split_path(
                coverage_eval[name]['branches'][key],
                coverage_map['branches']
            )
    return results


def _split_path(coverage_eval, coverage_map):
    results = {}
    for path, eval_ in coverage_eval.items():
        results[path] = _split_fn(eval_, coverage_map[path])
    return results


def _split_fn(coverage_eval, coverage_map):
    results = {}
    for fn, map_ in coverage_map.items():
        results[fn] = [i for i in map_ if int(i) in coverage_eval]
    return results


# TODO below here

def calculate_pct(coverage_eval):
    coverage_eval = split_by_fn(coverage_eval)


def generate_report(coverage_eval):
    '''Converts coverage evaluation into highlight data suitable for the GUI'''
    report = {
        'highlights': {},
        'coverage': {},
        'sha1': {}
    }
    coverage_eval = split_by_fn(coverage_eval)
    for name, coverage in coverage_eval.items():
        report['highlights'][name] = {}
        report['coverage'][name] = {'pct': {}}

#         for path in [i for i in coverage if i != "pct"]:
#             coverage_map = build.get(name)['coverageMap'][path]
#             report['highlights'][name][path] = []
#             for fn_name, lines in coverage_map.items():
#                 # if function has 0% or 100% coverage, highlight entire function
#                 report['coverage'][name][fn_name] = coverage[path][fn_name]['pct']
#                 if coverage[path][fn_name]['pct'] in (0, 1):
#                     color = "green" if coverage[path][fn_name]['pct'] else "red"
#                     start, stop = sources.get_fn_offset(path, fn_name)
#                     report['highlights'][name][path].append(
#                         (start, stop, color, "")
#                     )
#                     continue
#                 # otherwise, highlight individual statements
#                 for i, ln in enumerate(lines):
#                     if i in coverage[path][fn_name]['tx']:
#                         color = "green"
#                     elif i in coverage[path][fn_name]['true']:
#                         color = "yellow" if _evaluate_branch(path, ln) else "orange"
#                     elif i in coverage[path][fn_name]['false']:
#                         color = "orange" if _evaluate_branch(path, ln) else "yellow"
#                     else:
#                         color = "red"
#                     report['highlights'][name][path].append(
#                         (ln['offset'][0], ln['offset'][1], color, "")
#                     )
#     return report


# TODO - make sure GUI works with new coverage map format

# def _evaluate_branch(path, ln):
#     source = sources.get(path)
#     start, stop = ln['offset']
#     try:
#         idx = _maxindex(source[:start])
#     except Exception:
#         return False

#     # remove comments, strip whitespace
#     before = source[idx:start]
#     for pattern in (r'\/\*[\s\S]*?\*\/', r'\/\/[^\n]*'):
#         for i in re.findall(pattern, before):
#             before = before.replace(i, "")
#     before = before.strip("\n\t (")

#     idx = source[stop:].index(';')+len(source[:stop])
#     if idx <= stop:
#         return False
#     after = source[stop:idx].split()
#     after = next((i for i in after if i != ")"), after[0])[0]
#     if (
#         (before[-2:] == "if" and after == "|") or
#         (before[:7] == "require" and after in (")", "|", ","))
#     ):
#         return True
#     return False


# def _maxindex(source):
#     comp = [i for i in [";", "}", "{"] if i in source]
#     return max([source.rindex(i) for i in comp])+1
