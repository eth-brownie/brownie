import functools
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Dict, Final, List, Optional

from web3 import Web3


class BrownieMiddlewareABC(ABC):
    """
    Base ABC for all middlewares.

    This class must be inherited in order for a middleware to be discovered
    and added to the `web3` object upon connecting to a network.
    """

    def __init__(self, w3: Web3) -> None:
        """
        Initialize the middleware.

        Subclasses may optionally include this method. It is called only once,
        when the middleware is being added.
        """
        self.w3: Final = w3

    @classmethod
    @abstractmethod
    def get_layer(cls, w3: Web3, network_type: str) -> Optional[int]:
        """
        Return the target layer of this middleware.

        All builtin middlewares are considered to be on layer 0. Middlewares are called in
        ascending order prior to the request, and descending order after the request.
        """
        raise NotImplementedError

    def __call__(self, make_request: Callable, w3: Web3) -> Callable:
        """
        Receive the initial middleware request and return `process_request`.

        Subclasses should NOT include this method.
        """
        return functools.partial(self.process_request, make_request)

    @abstractmethod
    def process_request(self, make_request: Callable, method: str, params: List) -> Dict:
        """
        Process an RPC request.

        Data is pre-processed, sent onward via `make_request`, processed further and returned.
        See https://web3py.readthedocs.io/en/stable/internals.html#middlewares for more info.

        Arguments
        ---------
        method : str
            A string representing the JSON-RPC method that is being called.
        params : List
            An iterable of the parameters for the JSON-RPC method being called.

        Returns
        -------
        Dict
            A dictionary containing either a 'result' key in the case
            of success, or an 'error' key in the case of failure.
        """
        raise NotImplementedError

    def uninstall(self) -> None:
        """
        Uninstall a middleware.

        Subclasses may optionally include this method if any cleanup is required
        when they are removed. Note that you must not assume network connectivity
        when this method is called.
        """
        pass


def get_middlewares(web3: Web3, network_type: str) -> Dict:
    """
    Get a list of middlewares to be used for the given web3 object.

    Arguments
    ---------
    web3 : Web3
        The active web3 object, already connected to the current network.
    network_type : str
        One of "live" or "development".
    """
    middleware_layers: Dict[int, List] = {}
    for obj in _middlewares:
        layer = obj.get_layer(web3, network_type)
        if layer is not None:
            middleware_layers.setdefault(layer, []).append(obj)

    return middleware_layers


# this must go down here to prevent a circ import issue
from brownie.network.middlewares._setup import load_middlewares

_middlewares: Final = load_middlewares()
