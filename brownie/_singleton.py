#!/usr/bin/python3
from typing import Any, Dict, Tuple


class _Singleton(type):

    _instances: Dict = {}

    def __call__(cls, *args: Tuple, **kwargs: Dict) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
