#!/usr/bin/python3

from copy import deepcopy


_coverage_eval = {}
_cached = {}
_active_txhash = set()


def add(txhash, coverage_eval):
    _coverage_eval[txhash] = coverage_eval
    _active_txhash.add(txhash)


def add_cached(txhash, coverage_eval):
    _cached[txhash] = coverage_eval


def add_from_cached(txhash, active=True):
    if txhash in _cached:
        _coverage_eval[txhash] = _cached.pop(txhash)
        if active:
            _active_txhash.add(txhash)
    return txhash in _coverage_eval


def get_and_clear_active():
    result = sorted(_active_txhash)
    _active_txhash.clear()
    return result


def get_all():
    return {**_cached, **_coverage_eval}


def get_merged():
    '''Merges multiple coverage evaluation dicts.

    Arguments:
        coverage_eval_list: A list of coverage eval dicts.

    Returns: coverage eval dict.
    '''
    if not _coverage_eval:
        return {}
    coverage_eval_list = list(_coverage_eval.values())
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


def clear():
    _coverage_eval.clear()
    _cached.clear()
    _active_txhash.clear()
