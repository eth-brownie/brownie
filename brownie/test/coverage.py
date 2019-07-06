#!/usr/bin/python3

from copy import deepcopy

from brownie.types.types import _Singleton


class Coverage(metaclass=_Singleton):

    def __init__(self):
        self._coverage = {}

    def __contains__(self, txhash):
        return txhash in self._coverage

    def __setitem__(self, txhash, coverage_eval):
        self._coverage[txhash] = coverage_eval

    def get(self):
        return self._coverage

    def get_merged(self):
        '''Merges multiple coverage evaluation dicts.

        Arguments:
            coverage_eval_list: A list of coverage eval dicts.

        Returns: coverage eval dict.
        '''
        if not self._coverage:
            return {}
        coverage_eval_list = list(self._coverage.values())
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
