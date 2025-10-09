"""This script is the entrypoint for brownie's test suite.

In order to support eth-typing v5, we must patch eth-typing for testing.
pytest-ethereum is an unmaintained yet critical dependency of our testing flow
and requires a NewType, `ContractName` which was removed in eth-typing v5.

We must be sure it is patched before pytest starts up and attempts
to load any plugins.
"""

import sys
from typing import NewType

import eth_typing
import pytest

# Patch eth_typing (if the currently installed version is missing ContractName)
if not hasattr(eth_typing, "ContractName"):
    eth_typing.ContractName = NewType("ContractName", str)

# Now run pytest, forwarding all CLI arguments
sys.exit(pytest.main(sys.argv[1:]))
