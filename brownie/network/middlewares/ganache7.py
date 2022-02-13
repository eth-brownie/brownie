from typing import Callable, Dict, List, Optional

from web3 import Web3

from brownie.network.middlewares import BrownieMiddlewareABC


class Ganache7MiddleWare(BrownieMiddlewareABC):
    @classmethod
    def get_layer(cls, w3: Web3, network_type: str) -> Optional[int]:
        if w3.clientVersion.lower().startswith("ganache/v7"):
            return -100
        else:
            return None

    def process_request(self, make_request: Callable, method: str, params: List) -> Dict:
        if method == "eth_sendTransaction" and "nonce" in params[0]:
            # ganache 7 allows broadcasting tx's with a too-high nonce, which then
            # leaves brownie waiting forever for a tx that doesn't confirm
            actual = int(params[0]["nonce"], 16)
            expected = self.w3.eth.get_transaction_count(params[0]["from"])
            if expected < actual:
                raise ValueError(
                    f"Nonce too high. Expected nonce to be {expected} but got {actual}."
                )

        result = make_request(method, params)

        # reformat failed eth_call / eth_sendTransaction output to mimick that of Ganache 6.x
        # yes, this is hacky and awful and in the future we should stop supporting
        # the older version of ganache. but doing so will cause unexpected issues
        # in projects that are still pinned to the old verion, so for now we support
        # both and simply raise a warning of a pending deprecation.
        if method in ("eth_sendTransaction", "eth_sendRawTransaction") and "error" in result:
            data = result["error"]["data"]
            data["error"] = data.pop("message")
            result["error"]["data"] = {data.pop("hash"): data}

        if method == "eth_call" and "error" in result:
            # "VM Exception while processing transaction: revert {message}"
            msg = result["error"]["message"].split(": ", maxsplit=1)
            data = {"error": "revert", "reason": msg[7:]}
            result["error"]["data"] = {"0x": data}

        return result
