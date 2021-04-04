import queue
from typing import Callable, Dict, List, Optional

from brownie.network._multicall import ContractCallPromise, MulticallContractDeployer
from brownie.network.middlewares import BrownieMiddlewareABC


class FlushableQueue(queue.SimpleQueue):
    def get_all(self, *args, **kwargs):
        items = []
        while not self.empty():
            items.append(self.get())
        return items


class MulticallMiddleware(BrownieMiddlewareABC):
    def __init__(self, make_request, w3):
        self.queue = FlushableQueue()
        self._is_multicall_deployed = False
        self._multicall_addr = None

        self.make_request = make_request
        self.w3 = w3

    def process_request(self, make_request: Callable, method: str, params: List) -> Dict:
        # TODO: if not called from a multicall block, do nothing and pass on the request
        promise = ContractCallPromise(method, params)
        self.queue.put(promise)
        if self._needs_execution(method, params):
            results = self._execute()
            # should return the last result
        return {}

    def _execute(self):
        if self._needs_multicall_contract_deployed():
            self._multicall_addr = MulticallContractDeployer().deploy()
        calls = self.queue.get_all()
        # TODO: do the multicall, return the results
        return []

    def _needs_execution(self, method: str, params: List) -> bool:
        """_needs_execution determines if an actual eth_call must be made.

        If any item in `params` is a ContractCallPromise, we need to execute so we can get its value.

        This could be a standalone function, but we're including it as part of the middleware
        in case we want to execute or not based on the state of the queue.
        """
        for param in params:
            if isinstance(param, ContractCallPromise):
                return True
        return False

    def _needs_multicall_contract_deployed(self):
        """deploy deploys the multicall contract.

        args and kwargs get passed through to _deploy.

        This should only be run in dev."""
        if self._multicall_contract_addr and self._is_multicall_deployed:
            return False
        elif not _is_development():
            return False
        else:
            return True


def _is_development():
    # TODO: check _config.CONFIG to see if we're running in dev or not
    return True
