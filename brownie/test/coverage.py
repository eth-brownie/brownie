#!/usr/bin/python3

from copy import deepcopy

from brownie.project import build


def merge(coverage_eval_dict):
    '''Merges multiple coverage evaluation dicts.

    Arguments:
        coverage_eval_list: A list of coverage eval dicts.

    Returns: coverage eval dict.
    '''
    coverage_eval_list = list(coverage_eval_dict.values())
    merged_eval = deepcopy(coverage_eval_list.pop())
    for coverage_eval in coverage_eval_list:
        for name in coverage_eval:
            if name not in merged_eval:
                merged_eval[name] = coverage_eval[name]
                continue
            for path, map_ in coverage_eval[name].items():
                if path not in merged_eval[name]:
                    merged_eval[name][path] = map_
                    continue
                for i in range(3):
                    merged_eval[name][path][i] = set(merged_eval[name][path][i]).union(map_[i])
    return merged_eval


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
        map_ = build.get(name)['coverageMap']
        results[name] = dict((k, _split(v, map_, k)) for k, v in coverage_eval[name].items())
    return results


def _split(coverage_eval, coverage_map, key):
    results = {}
    for fn, map_ in coverage_map['statements'][key].items():
        results[fn] = [[i for i in map_ if int(i) in coverage_eval[0]], [], []]
    for fn, map_ in coverage_map['branches'][key].items():
        results[fn][1] = [i for i in map_ if int(i) in coverage_eval[1]]
        results[fn][2] = [i for i in map_ if int(i) in coverage_eval[2]]
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
            coverage_eval[name],
            coverage_map['statements']
        )
        r['branches'], r['totals']['branches'] = _branch_totals(
            coverage_eval[name],
            coverage_map['branches']
        )
    return results


def _statement_totals(coverage_eval, coverage_map):
    result = {}
    count, total = 0, 0
    for path, fn in [(k, x) for k, v in coverage_eval.items() for x in v]:
        count += len(coverage_eval[path][fn][0])
        total += len(coverage_map[path][fn])
        result[fn] = (len(coverage_eval[path][fn][0]), len(coverage_map[path][fn]))
    return result, (count, total)


def _branch_totals(coverage_eval, coverage_map):
    result = {}
    final = [0, 0, 0]
    for path, fn in [(k, x) for k, v in coverage_map.items() for x in v]:
        if path not in coverage_eval:
            true, false = 0, 0
        else:
            true = len(coverage_eval[path][fn][2])
            false = len(coverage_eval[path][fn][1])
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
            coverage_eval[name],
            coverage_map['statements']
        )
        results['branches'][name] = _branch_highlights(
            coverage_eval[name],
            coverage_map['branches']
        )
    return results


def _statement_highlights(coverage_eval, coverage_map):
    results = dict((i, []) for i in coverage_map)
    for path, fn in [(k, x) for k, v in coverage_map.items() for x in v]:
        results[path].extend([
            list(offset) + [_statement_color(i, coverage_eval, path), ""]
            for i, offset in coverage_map[path][fn].items()
        ])
    return results


def _statement_color(i, coverage_eval, path):
    if path not in coverage_eval or int(i) not in coverage_eval[path][0]:
        return "red"
    return "green"


def _branch_highlights(coverage_eval, coverage_map):
    results = dict((i, []) for i in coverage_map)
    for path, fn in [(k, x) for k, v in coverage_map.items() for x in v]:
        results[path].extend([
            list(offset[:2]) + [_branch_color(int(i), coverage_eval, path, offset[2]), ""]
            for i, offset in coverage_map[path][fn].items()
        ])
    return results


def _branch_color(i, coverage_eval, path, jump):
    if path not in coverage_eval:
        return "red"
    if i in coverage_eval[path][2]:
        if i in coverage_eval[path][1]:
            return "green"
        return "yellow" if jump else "orange"
    if i in coverage_eval[path][1]:
        return "orange" if jump else "yellow"
    return "red"
