from typing import Callable, Dict, List, Optional

from web3 import Web3

from brownie.network.middlewares import BrownieMiddlewareABC


class HardhatMiddleWare(BrownieMiddlewareABC):
    @classmethod
    def get_layer(cls, w3: Web3, network_type: str) -> Optional[int]:
        if w3.clientVersion.lower().startswith("hardhat"):
            return -100
        else:
            return None

    def process_request(self, make_request: Callable, method: str, params: List) -> Dict:
        result = make_request(method, params)

        # modify Hardhat transaction error to mimick the format that Ganache uses
        if method == "eth_sendTransaction" and "error" in result:
            txid = self.w3.eth.getBlock("latest")["transactions"][0]
            data: Dict = {}
            result["error"]["data"] = {txid.hex(): data}
            message = result["error"]["message"].split(": ", maxsplit=1)[1]
            if message.startswith("revert"):
                data.update(error="revert", reason=message[7:])
            else:
                data["error"] = message
        return result
