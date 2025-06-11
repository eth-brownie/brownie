#!/usr/bin/python3
from typing import Dict


class _Singleton(type):

    _instances: Dict = {}

    def __call__(cls, *args, **kwargs):
        # NOTE counterintuitively, when you supply type hints for a metaclass call method,
        #      it breaks the standard typing for the created instances. Do not add types here.
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
