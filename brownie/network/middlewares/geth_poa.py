from typing import Callable, Dict, List, Optional

from web3 import Web3
from web3.exceptions import ExtraDataLengthError
from web3.middleware import geth_poa_middleware

from brownie.network.middlewares import BrownieMiddlewareABC


class GethPOAMiddleware(BrownieMiddlewareABC):
    @classmethod
    def get_layer(cls, w3: Web3, network_type: str) -> Optional[int]:
        # NOTE: We check `0` because Ganache sometimes injects a block of their own.
        # It doesn't have the extra data that we are checking for.
        # We also check `"latest"` because On Polygon networks, anvil in forked
        # development mode doesn't throw ExtraDataLengthError on the first block.
        block_idents = ("latest",) if network_type == "live" else (0, "latest")
        try:
            for block_ident in block_idents:
                w3.eth.get_block(block_ident)
            return None
        except ExtraDataLengthError:
            return -1

    def process_request(self, make_request: Callable, method: str, params: List) -> Dict:
        middleware_fn = geth_poa_middleware(make_request, self.w3)
        return middleware_fn(method, params)
