#!/usr/bin/python3

from .loader import (  # NOQA 401
    check_for_project,
    new,
    load,
    compile_source
)

__all__ = ['__project']

__project = None
