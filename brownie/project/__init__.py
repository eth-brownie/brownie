#!/usr/bin/python3

from .main import (  # NOQA 401
    check_for_project,
    compile_source,
    get_loaded_projects,
    load,
    new,
    pull,
)
from .scripts import run

__all__ = ["run"]

__console_dir__ = ["run", "new", "pull", "load", "compile_source"]
