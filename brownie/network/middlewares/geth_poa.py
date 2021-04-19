from typing import Callable, Dict, List, Optional

from web3 import Web3
from web3.exceptions import ExtraDataLengthError
from web3.middleware import geth_poa_middleware

from brownie.network.middlewares import BrownieMiddlewareABC


class GethPOAMiddleware(BrownieMiddlewareABC):
    @classmethod
    def get_layer(cls, w3: Web3, network_type: str) -> Optional[int]:
        try:
            w3.eth.get_block("latest")
            return None
        except ExtraDataLengthError:
            return -1

    def process_request(self, make_request: Callable, method: str, params: List) -> Dict:
        middleware_fn = geth_poa_middleware(make_request, self.w3)
        return middleware_fn(method, params)
