"""
This helper file exists so we can use `__file__`, which does not exist when a file is compiled with mypyc.
"""

from brownie._c_constants import Path, import_module
from brownie.network.middlewares import BrownieMiddlewareABC


def load_middlewares() -> list[type[BrownieMiddlewareABC]]:
    """
    Load middleware classes from all modules within `brownie/networks/middlewares/`.

    To be included the module name must not begin with `_` and the middleware
    must subclass :class:`~BrownieMiddlewareABC`.
    """
    middlewares = []
    for path in Path(__file__).parent.glob("[!_]*.py"):
        module = import_module(f"{__package__}.{path.stem}")
        middlewares.extend(
            obj
            for obj in module.__dict__.values()
            if isinstance(obj, type)
            and obj.__module__ == module.__name__
            and BrownieMiddlewareABC in obj.mro()
        )
    return middlewares
