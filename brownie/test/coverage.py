#!/usr/bin/python3

from typing import Dict, Final, List, Optional, Set

from eth_typing import HexStr

from brownie._c_constants import deepcopy
from brownie.typing import ContractName

CoverageEval = Dict[ContractName, Dict[str, Dict[int, Set]]]

# Coverage evaluation is stored on a per-tx basis. We use a special "coverage hash"
# with additional inforarmation included to ensure no two transactions will produce
# the same hash.

_coverage_eval: Final[Dict[str, CoverageEval]] = {}


# Because querying traces is slow, old coverage data is cached. Prior to evaluating
# a transaction, a call to `_check_cached` confirms if the transaction was already
# been evaluated in a previous session.

_cached_coverage_eval: Final[Dict[str, CoverageEval]] = {}

# We track coverage hashes for the currently active test module so we know which
# data to look at in order to determine coverage for that module.

_active_module_coverage_hashes: Final[Set[HexStr]] = set()


def get_coverage_eval() -> Dict[str, Dict]:
    """Returns all coverage data, active and cached."""
    return {**_cached_coverage_eval, **_coverage_eval}


def get_merged_coverage_eval(cov_eval: Optional[Dict[str, CoverageEval]] = None) -> CoverageEval:
    """Merges and returns all active coverage data as a single dict.

    Returns: coverage eval dict.
    """
    if cov_eval is None:
        cov_eval = _coverage_eval
    if not cov_eval:
        return {}  # type: ignore [return-value]
    coverage_eval_list = list(cov_eval.values())
    merged_eval = deepcopy(coverage_eval_list.pop())
    for coverage_eval in coverage_eval_list:
        for name in coverage_eval:
            if name not in merged_eval:
                merged_eval[name] = coverage_eval[name]
                continue
            eval_for_name = merged_eval[name]
            for path, map_ in coverage_eval[name].items():
                if path not in eval_for_name:
                    eval_for_name[path] = map_
                    continue
                eval_for_path = eval_for_name[path]
                for i in range(3):
                    eval_for_path[i] = set(eval_for_path[i]).union(map_[i])
    return merged_eval


def clear() -> None:
    """Clears all coverage eval data."""
    _coverage_eval.clear()
    _cached_coverage_eval.clear()
    _active_module_coverage_hashes.clear()


def _add_transaction(coverage_hash: HexStr, coverage_eval: CoverageEval) -> None:
    # Add coverage data for a transaction and include the hash in the list of active hashes
    _coverage_eval[coverage_hash] = coverage_eval
    _active_module_coverage_hashes.add(coverage_hash)


def _add_cached_transaction(coverage_hash: HexStr, coverage_eval: CoverageEval) -> None:
    # Add a cached transaction
    _cached_coverage_eval[coverage_hash] = coverage_eval


def _check_cached(coverage_hash: HexStr, active: bool = True) -> bool:
    # Checks if a hash is present within the cache, and if yes add it to the active data
    if coverage_hash in _cached_coverage_eval:
        _coverage_eval[coverage_hash] = _cached_coverage_eval.pop(coverage_hash)
        if active:
            _active_module_coverage_hashes.add(coverage_hash)
    return coverage_hash in _coverage_eval


def _get_active_txlist() -> List[HexStr]:
    # Return a list of coverage hashes that are currently marked as active
    return sorted(_active_module_coverage_hashes)


def _clear_active_txlist() -> None:
    # Clear the active coverage hash list
    _active_module_coverage_hashes.clear()
