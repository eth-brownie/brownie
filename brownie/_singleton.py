#!/usr/bin/python3
from typing import Any, Dict, Tuple


class _Singleton(type):

    _instances: Dict = {}

    def __call__(self, *args: Tuple, **kwargs: Dict) -> Any:
        if self not in self._instances:
            self._instances[self] = super(_Singleton, self).__call__(*args, **kwargs)
        return self._instances[self]
