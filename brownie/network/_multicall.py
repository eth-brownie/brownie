from typing import List, Optional
from brownie._singleton import _Singleton
from brownie._config import CONFIG


class PromiseAlredyResolvedError(Exception):
    pass


class ContractCallPromise:
    """ ContractCallPromise represents a contract call that will be run in the future
    """

    def __init__(self, method: str, params: List):
        self.method = method
        self.params = params
        self.resolved = False
        self.result = None

    def resolve(self, value):
        if self.resolved:
            raise PromiseAlredyResolvedError(f"{self._name} already resolved")
        self.resolved = True
        self.result = value

    @property
    def _name(self):
        return f"{self.method}({','.join(map(str, self.params))})"


class MulticallContractDeployer(_Singleton):
    def deploy(self, w3) -> str:
        """deploy deploys the multicall contract and returns the address

        Returns:
            str: address where contract is deployed
        """
        return "0xabcdefg"


class MulticallContextManager:
    def __init__(self):
        self.queue = queue.SimpleQueue()
        print("init method")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        return self

    def _execute(self):
        """pops everything, runs multicall, gets result, returns"""
        pass

multicall = MulticallContextManager

def multicall():
    print("entering multicall manager")
    yield
    print("exiting multicall manager")
