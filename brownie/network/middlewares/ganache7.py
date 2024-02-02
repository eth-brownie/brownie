from typing import Callable, Dict, List, Optional

from web3 import Web3

from brownie.network.middlewares import BrownieMiddlewareABC


class Ganache7MiddleWare(BrownieMiddlewareABC):
    @classmethod
    def get_layer(cls, w3: Web3, network_type: str) -> Optional[int]:
        if w3.client_version.lower().startswith("ganache/v7"):
            return -100
        else:
            return None

    def process_request(self, make_request: Callable, method: str, params: List) -> Dict:
        result = make_request(method, params)

        # reformat failed eth_call / eth_sendTransaction output to mimick that of Ganache 6.x
        # yes, this is hacky and awful and in the future we should stop supporting
        # the older version of ganache. but doing so will cause unexpected issues
        # in projects that are still pinned to the old verion, so for now we support
        # both and simply raise a warning of a pending deprecation.
        if (
            method in ("eth_sendTransaction", "eth_sendRawTransaction")
            and "error" in result
            and "data" in result["error"]
        ):
            data = result["error"]["data"]
            data["error"] = data.pop("message")
            data["program_counter"] = data.pop("programCounter")
            result["error"]["data"] = {data.pop("hash"): data}

        if (
            method == "eth_call"
            and "error" in result
            and result["error"].get("message", "").startswith("VM Exception")
        ):
            # "VM Exception while processing transaction: {reason} {message}"
            msg = result["error"]["message"].split(": ", maxsplit=1)[-1]
            if msg.startswith("revert"):
                data = {"error": "revert", "reason": result["error"]["data"]}
            else:
                data = {"error": msg, "reason": None}
            result["error"]["data"] = {"0x": data}

        return result
