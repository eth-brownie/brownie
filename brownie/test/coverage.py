#!/usr/bin/python3

from copy import deepcopy
from typing import Dict

# Coverage evaluation is stored on a per-tx basis. We use a special "coverage hash"
# with additional inforarmation included to ensure no two transactions will produce
# the same hash.

_coverage_eval: Dict[str, Dict] = {}


# Because querying traces is slow, old coverage data is cached. Prior to evaluating
# a transaction, a call to `_check_cached` confirms if the transaction was already
# been evaluated in a previous session.

_cached_coverage_eval: Dict[str, Dict] = {}

# We track coverage hashes for the currently active test module so we know which
# data to look at in order to determine coverage for that module.

_active_module_coverage_hashes: set = set()


def get_coverage_eval():
    """Returns all coverage data, active and cached."""
    return {**_cached_coverage_eval, **_coverage_eval}


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
    _cached_coverage_eval.clear()
    _active_module_coverage_hashes.clear()


def _add_transaction(coverage_hash, coverage_eval):
    # Add coverage data for a transaction and include the hash in the list of active hashes
    _coverage_eval[coverage_hash] = coverage_eval
    _active_module_coverage_hashes.add(coverage_hash)


def _add_cached_transaction(coverage_hash, coverage_eval):
    # Add a cached transaction
    _cached_coverage_eval[coverage_hash] = coverage_eval


def _check_cached(coverage_hash, active=True):
    # Checks if a hash is present within the cache, and if yes add it to the active data
    if coverage_hash in _cached_coverage_eval:
        _coverage_eval[coverage_hash] = _cached_coverage_eval.pop(coverage_hash)
        if active:
            _active_module_coverage_hashes.add(coverage_hash)
    return coverage_hash in _coverage_eval


def _get_active_txlist():
    # Return a list of coverage hashes that are currently marked as active
    return sorted(_active_module_coverage_hashes)


def _clear_active_txlist():
    # Clear the active coverage hash list
    _active_module_coverage_hashes.clear()
