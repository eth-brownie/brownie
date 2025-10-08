"""
Brownie is written in Python, but compiled to C using mypyc.

This file exists to hold C constants for commonly used external imports.

C constants let us bypass reference counting and are significantly more efficient to access.

Check out https://github.com/mypyc/mypyc for more info.
"""

import collections
import copy
import decimal
import hashlib
import importlib
import pathlib
import re
from typing import Final

import faster_eth_utils.toolz
import faster_hexbytes
import semantic_version
import ujson

# BUILTINS
# collections
defaultdict: Final = collections.defaultdict
deque: Final = collections.deque

# copy
deepcopy: Final = copy.deepcopy

# decimal
Decimal: Final = decimal.Decimal
getcontext: Final = decimal.getcontext

# hashlib
sha1: Final = hashlib.sha1

# importlib
import_module: Final = importlib.import_module

# pathlib
Path: Final = pathlib.Path

# re
regex_compile: Final = re.compile
regex_findall: Final = re.findall
regex_finditer: Final = re.finditer
regex_fullmatch: Final = re.fullmatch
regex_match: Final = re.match
regex_sub: Final = re.sub


# DEPENDENCIES
# faster_hexbytes
HexBytes: Final = faster_hexbytes.HexBytes

# semantic_version
NpmSpec: Final = semantic_version.NpmSpec
Version: Final = semantic_version.Version

# toolz
mapcat: Final = faster_eth_utils.toolz.mapcat

# ujson
ujson_dump: Final = ujson.dump
ujson_dumps: Final = ujson.dumps
ujson_load: Final = ujson.load
ujson_loads: Final = ujson.loads
