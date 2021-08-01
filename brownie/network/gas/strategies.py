import itertools
import threading
import time
import warnings
from typing import Dict, Generator

import requests

from brownie.convert import Wei
from brownie.exceptions import RPCRequestError
from brownie.network.web3 import web3

from .bases import BlockGasStrategy, SimpleGasStrategy, TimeGasStrategy

_gasnow_update = 0
_gasnow_data: Dict[str, int] = {}
_gasnow_lock = threading.Lock()


def _fetch_gasnow(key: str) -> int:
    global _gasnow_update
    with _gasnow_lock:
        time_since_update = int(time.time() - _gasnow_update)
        if time_since_update > 15:
            try:
                response = requests.get(
                    "https://www.gasnow.org/api/v3/gas/price?utm_source=brownie"
                )
                response.raise_for_status()
                data = response.json()["data"]
                _gasnow_update = data.pop("timestamp") // 1000
                _gasnow_data.update(data)
            except requests.exceptions.RequestException as exc:
                if time_since_update > 120:
                    raise
                warnings.warn(
                    f"{type(exc).__name__} while querying GasNow API. "
                    f"Last successful update was {time_since_update}s ago.",
                    RuntimeWarning,
                )

    return _gasnow_data[key]


class LinearScalingStrategy(TimeGasStrategy):
    """
    Gas strategy for linear gas price increase.

    Arguments
    ---------
    initial_gas_price : int
        The initial gas price to use in the first transaction
    max_gas_price : int
        The maximum gas price to use
    increment : float
        Multiplier applied to the previous gas price in order to determine the new gas price
    time_duration : int
        Number of seconds between transactions
    """

    def __init__(
        self,
        initial_gas_price: Wei,
        max_gas_price: Wei,
        increment: float = 1.125,
        time_duration: int = 30,
    ):
        super().__init__(time_duration)
        self.initial_gas_price = Wei(initial_gas_price)
        self.max_gas_price = Wei(max_gas_price)
        self.increment = increment

    def get_gas_price(self) -> Generator[Wei, None, None]:
        last_gas_price = self.initial_gas_price
        yield last_gas_price

        while True:
            last_gas_price = min(Wei(last_gas_price * self.increment), self.max_gas_price)
            yield last_gas_price


class ExponentialScalingStrategy(TimeGasStrategy):
    """
    Gas strategy for exponential increasing gas prices.

    The gas price for each subsequent transaction is calculated as the previous price
    multiplied by `1.1 ** n` where n is the number of transactions that have been broadcast.
    In this way the price increase starts gradually and ramps up until confirmation.

    Arguments
    ---------
    initial_gas_price : Wei
        The initial gas price to use in the first transaction
    max_gas_price : Wei
        The maximum gas price to use
    increment : float
        Multiplier applied to the previous gas price in order to determine the new gas price
    time_duration : int
        Number of seconds between transactions
    """

    def __init__(self, initial_gas_price: Wei, max_gas_price: Wei, time_duration: int = 30):
        super().__init__(time_duration)
        self.initial_gas_price = Wei(initial_gas_price)
        self.max_gas_price = Wei(max_gas_price)

    def get_gas_price(self) -> Generator[Wei, None, None]:
        last_gas_price = self.initial_gas_price
        yield last_gas_price

        for i in itertools.count(1):
            last_gas_price = Wei(last_gas_price * 1.1 ** i)
            yield min(last_gas_price, self.max_gas_price)


class GasNowStrategy(SimpleGasStrategy):
    """
    Gas strategy for determing a price using the GasNow API.

    GasNow returns 4 possible prices:

    rapid: the median gas prices for all transactions currently included
           in the mining block
    fast: the gas price transaction "N", the minimum priced tx currently
          included in the mining block
    standard: the gas price of the Max(2N, 500th) transaction in the mempool
    slow: the gas price of the max(5N, 1000th) transaction within the mempool

    Visit https://www.gasnow.org/ for more information on how GasNow
    calculates gas prices.
    """

    def __init__(self, speed: str = "fast"):
        if speed not in ("rapid", "fast", "standard", "slow"):
            raise ValueError("`speed` must be one of: rapid, fast, standard, slow")
        self.speed = speed

    def get_gas_price(self) -> int:
        return _fetch_gasnow(self.speed)


class GasNowScalingStrategy(BlockGasStrategy):
    """
    Block based scaling gas strategy using the GasNow API.

    The initial gas price is set according to `initial_speed`. The gas price
    for each subsequent transaction is increased by multiplying the previous gas
    price by `increment`, or increasing to the current `initial_speed` gas price,
    whichever is higher. No repricing occurs if the new gas price would exceed
    the current `max_speed` price as given by the API.
    """

    def __init__(
        self,
        initial_speed: str = "standard",
        max_speed: str = "rapid",
        increment: float = 1.125,
        block_duration: int = 2,
        max_gas_price: Wei = None,
    ):
        super().__init__(block_duration)
        if initial_speed not in ("rapid", "fast", "standard", "slow"):
            raise ValueError("`initial_speed` must be one of: rapid, fast, standard, slow")
        self.initial_speed = initial_speed
        self.max_speed = max_speed
        self.increment = increment
        self.max_gas_price = Wei(max_gas_price) or 2 ** 256 - 1

    def get_gas_price(self) -> Generator[int, None, None]:
        last_gas_price = _fetch_gasnow(self.initial_speed)
        yield last_gas_price

        while True:
            # increment the last price by `increment` or use the new
            # `initial_speed` value, whichever is higher
            initial_gas_price = _fetch_gasnow(self.initial_speed)
            incremented_gas_price = int(last_gas_price * self.increment)
            new_gas_price = max(initial_gas_price, incremented_gas_price)

            # do not exceed the current `max_speed` price
            max_gas_price = _fetch_gasnow(self.max_speed)
            last_gas_price = min(max_gas_price, new_gas_price, self.max_gas_price)
            yield last_gas_price


class GethMempoolStrategy(BlockGasStrategy):
    """
    Block based scaling gas strategy using the GraphQL and the Geth mempool.

    The yielded gas price is determined by sorting transactions in the mempool
    according to gas price, and returning the price of the transaction at `position`.
    This is the same technique used by the GasNow API.

    A position of 500 should place a transaction within the 2nd block to be mined.
    A position of 200 or less should place it within the next block.
    """

    def __init__(
        self,
        position: int = 500,
        graphql_endpoint: str = None,
        block_duration: int = 2,
        max_gas_price: Wei = None,
    ):
        super().__init__(block_duration)
        self.position = position
        if graphql_endpoint is None:
            graphql_endpoint = f"{web3.provider.endpoint_uri}/graphql"  # type: ignore
        self.graphql_endpoint = graphql_endpoint
        self.max_gas_price = Wei(max_gas_price) or 2 ** 256 - 1

    def get_gas_price(self) -> Generator[int, None, None]:
        query = "{ pending { transactions { gasPrice }}}"

        while True:
            response = requests.post(self.graphql_endpoint, json={"query": query})
            response.raise_for_status()
            if "error" in response.json():
                raise RPCRequestError("could not fetch mempool, run geth with `--graphql` flag")

            data = response.json()["data"]["pending"]["transactions"]

            prices = sorted((int(x["gasPrice"], 16) for x in data), reverse=True)

            yield min(prices[: self.position][-1], self.max_gas_price)
