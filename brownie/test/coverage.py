#!/usr/bin/python3

from copy import deepcopy
from typing import Dict

_coverage_eval: Dict[str, Dict] = {}
_cached: Dict[str, Dict] = {}
_active_txhash: set = set()


def get_coverage_eval():
    """Returns all coverage data, active and cached."""
    return {**_cached, **_coverage_eval}


def get_merged_coverage_eval(cov_eval=None):
    """Merges and returns all active coverage data as a single dict.

    Returns: coverage eval dict.
    """
    if cov_eval is None:
        cov_eval = _coverage_eval
    if not cov_eval:
        return {}
    coverage_eval_list = list(cov_eval.values())
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
    """Clears all coverage eval data."""
    _coverage_eval.clear()
    _cached.clear()
    _active_txhash.clear()


def _add_transaction(txhash, coverage_eval):
    # Adds coverage eval data
    _coverage_eval[txhash] = coverage_eval
    _active_txhash.add(txhash)


def _add_cached_transaction(txhash, coverage_eval):
    # Adds coverage data to the cache
    _cached[txhash] = coverage_eval


def _check_cached(txhash, active=True):
    # Checks if a tx hash is present within the cache, and if yes adds it to the active data
    if txhash in _cached:
        _coverage_eval[txhash] = _cached.pop(txhash)
        if active:
            _active_txhash.add(txhash)
    return txhash in _coverage_eval


def _get_active_txlist():
    # Returns a list of coverage hashes that are currently marked as active
    return sorted(_active_txhash)


def _clear_active_txlist():
    # Clears the active coverage hash list
    _active_txhash.clear()
