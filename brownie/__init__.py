#!/usr/bin/python3

from brownie.network import (
    accounts,
    network,
    rpc,
    web3
)
from brownie.project import (
    project,
    __project
)

__all__ = [
    'accounts',
    'network',
    'rpc',
    'web3',
    '__project',
    'project',
    'CONFIG'
]

import brownie.config as _config
CONFIG = _config.CONFIG
