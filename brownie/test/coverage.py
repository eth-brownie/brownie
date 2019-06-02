#!/usr/bin/python3

from copy import deepcopy
import json
from pathlib import Path

from brownie.project import build


def analyze(history, coverage_eval={}):
    '''Analyzes contract coverage.

    Arguments:
        history: List of TransactionReceipt objects.

    Returns:
        { "ContractName":
            "statements": {"path/to/file": [index, ..], .. },
            "branches": {
                "true": {"path/to/file": [index, ..], .. },
            "false": {"path/to/file": [index, ..], .. },
            }
        }'''
    for tx in filter(lambda k: k.trace, history):
        build_json = {'contractName': None}
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
    coverage_eval = [json.load(Path(i).open())['coverage'] for i in coverage_files]
    return merge(coverage_eval)


def merge(coverage_eval_list):
    '''Merges multiple coverage evaluation dicts.

    Arguments:
        coverage_eval_list: A list of coverage eval dicts.

    Returns: coverage eval dict.
    '''
    merged_eval = deepcopy(coverage_eval_list[0])
    for cov in coverage_eval_list[1:]:
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
    '''Splits a coverage eval dict so that coverage indexes are stored by contract
    function. Once done, the dict is no longer compatible with other methods in this module.

    Original format:
        {"path/to/file": [index, ..], .. }

    New format:
        {"path/to/file": { "ContractName.functionName": [index, .. ], .. }
    '''
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


def get_totals(coverage_eval):
    '''Returns a modified coverage eval dict showing counts and totals for each
    contract function.

    Arguments:
        coverage_eval: Standard coverage evaluation dict

    Returns:
        { "ContractName": {
            "statements": {
                "path/to/file": {
                    "ContractName.functionName": (count, total), ..
                }, ..
            },
            "branches" {
                "path/to/file": {
                    "ContractName.functionName": (true count, false count, total), ..
                }, ..
            }
        }'''
    coverage_eval = split_by_fn(coverage_eval)
    results = dict((i, {
        'statements': {},
        'totals': {'statements': 0, 'branches': [0, 0]},
        'branches': {'true': {}, 'false': {}}}
    ) for i in coverage_eval)
    for name in coverage_eval:
        coverage_map = build.get(name)['coverageMap']
        r = results[name]
        r['statements'], r['totals']['statements'] = _statement_totals(
            coverage_eval[name]['statements'],
            coverage_map['statements']
        )
        r['branches'], r['totals']['branches'] = _branch_totals(
            coverage_eval[name]['branches'],
            coverage_map['branches']
        )
    return results


def _statement_totals(coverage_eval, coverage_map):
    result = {}
    count, total = 0, 0
    for path, fn in [(k, x) for k, v in coverage_eval.items() for x in v]:
        count += len(coverage_eval[path][fn])
        total += len(coverage_map[path][fn])
        result[fn] = (len(coverage_eval[path][fn]), len(coverage_map[path][fn]))
    return result, (count, total)


def _branch_totals(coverage_eval, coverage_map):
    result = {}
    final = [0, 0, 0]
    for path, fn in [(k, x) for k, v in coverage_map.items() for x in v]:
        true = len(coverage_eval['true'][path][fn])
        false = len(coverage_eval['false'][path][fn])
        total = len(coverage_map[path][fn])
        result[fn] = (true, false, total)
        for i in range(3):
            final[i] += result[fn][i]
    return result, final


def get_highlights(coverage_eval):
    '''Returns a highlight map formatted for display in the GUI.

    Arguments:
        coverage_eval: coverage evaluation dict

    Returns:
        {
            "statements": {
                "ContractName": {"path/to/file": [start, stop, color, msg .. ], .. },
            },
            "branches": {
                "ContractName": {"path/to/file": [start, stop, color, msg .. ], .. },
            }
        }'''
    results = {
        'statements': {},
        'branches': {}
    }
    for name in coverage_eval:
        coverage_map = build.get(name)['coverageMap']
        results['statements'][name] = _statement_highlights(
            coverage_eval[name]['statements'],
            coverage_map['statements']
        )
        results['branches'][name] = _branch_highlights(
            coverage_eval[name]['branches'],
            coverage_map['branches']
        )
    return results


def _statement_highlights(coverage_eval, coverage_map):
    results = dict((i, []) for i in coverage_map)
    for path, fn in [(k, x) for k, v in coverage_map.items() for x in v]:
        results[path].extend([
            coverage_map[path][fn][i]+["green" if int(i) in coverage_eval[path] else "red", ""]
            for i in coverage_map[path][fn]
        ])
    return results


def _branch_highlights(coverage_eval, coverage_map):
    results = dict((i, []) for i in coverage_map)
    for path, fn in [(k, x) for k, v in coverage_map.items() for x in v]:
        results[path].extend([
            coverage_map[path][fn][i]+[_branch_color(int(i), coverage_eval, path), ""]
            for i in coverage_map[path][fn]
        ])
    return results


def _branch_color(i, coverage_eval, path):
    if i in coverage_eval['true'][path]:
        if i in coverage_eval['false'][path]:
            return "green"
        return "yellow"
    if i in coverage_eval['false'][path]:
        return "orange"
    return "red"
