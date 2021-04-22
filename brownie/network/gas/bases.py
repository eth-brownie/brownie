import inspect
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Generator, Iterator, Union

from brownie.network.web3 import web3


class GasABC(ABC):
    """
    Base ABC for all gas strategies.

    This class should not be directly subclassed from. Instead, use
    `SimpleGasStrategy`, `BlockGasStrategy` or `TimeGasStrategy`.
    """

    @abstractmethod
    def get_gas_price(self) -> Union[Generator[int, None, None], int]:
        raise NotImplementedError


class ScalingGasABC(GasABC):
    """
    Base ABC for scaling gas strategies.

    This class should not be directly subclassed from.
    Instead, use `BlockGasStrategy` or `TimeGasStrategy`.
    """

    duration: int

    def __new__(cls, *args: Any, **kwargs: Any) -> object:
        obj = super().__new__(cls)
        if not inspect.isgeneratorfunction(cls.get_gas_price):
            raise TypeError("Scaling strategy must implement get_gas_price as a generator function")
        return obj

    @abstractmethod
    def interval(self) -> int:
        """
        Return "now" as it relates to the scaling strategy.

        This can be e.g. the current time or block height. It is used in combination
        with `duration` to determine when to rebroadcast a transaction.
        """
        raise NotImplementedError

    def _loop(self, receipt: Any, gas_iter: Iterator) -> None:
        # retain the initial `silent` setting - tx's with required_confs=0 are set to
        # silent prior to confirmation, so if we don't do this the console output is
        # silenced by the 2nd replacement
        silent = receipt._silent

        while web3.eth.get_transaction_count(str(receipt.sender)) < receipt.nonce:
            # do not run scaling strategy while prior tx's are still pending
            time.sleep(5)

        latest_interval = self.interval()
        while True:
            if web3.eth.get_transaction_count(str(receipt.sender)) > receipt.nonce:
                break

            if self.interval() - latest_interval >= self.duration:
                gas_price = next(gas_iter)
                if gas_price >= int(receipt.gas_price * 1.1):
                    try:
                        receipt = receipt.replace(gas_price=gas_price, silent=silent)
                        latest_interval = self.interval()
                    except ValueError:
                        pass
            time.sleep(2)

    def run(self, receipt: Any, gas_iter: Iterator) -> None:
        thread = threading.Thread(
            target=self._loop,
            args=(receipt, gas_iter),
            daemon=True,
            name=f"Gas strategy {receipt.txid}",
        )
        thread.start()


class SimpleGasStrategy(GasABC):
    """
    Abstract base class for simple gas strategies.

    Simple gas strategies are called once to provide a gas price
    at the time a transaction is broadcasted. Transactions using simple
    gas strategies are not automatically rebroadcasted.

    Subclass from this ABC to implement your own simple gas strategy.
    """

    @abstractmethod
    def get_gas_price(self) -> int:
        """
        Return the initial gas price for a transaction.

        Returns
        -------
        int
            Gas price, given as an integer in wei.
        """
        raise NotImplementedError


class BlockGasStrategy(ScalingGasABC):
    """
    Abstract base class for block gas strategies.

    Block gas strategies are called every `block_duration` blocks and
    can be used to automatically rebroadcast a pending transaction with
    a higher gas price.

    Subclass from this ABC to implement your own block gas strategy.
    """

    duration = 2

    def __init__(self, block_duration: int = 2) -> None:
        self.duration = block_duration

    def interval(self) -> int:
        return web3.eth.block_number

    @abstractmethod
    def get_gas_price(self) -> Generator[int, None, None]:
        """
        Generator function to yield gas prices for a transaction.

        Returns
        -------
        int
            Gas price, given as an integer in wei.
        """
        raise NotImplementedError


class TimeGasStrategy(ScalingGasABC):
    """
    Abstract base class for time gas strategies.

    Time gas strategies are called every `time_duration` seconds and
    can be used to automatically rebroadcast a pending transaction with
    a higher gas price.

    Subclass from this ABC to implement your own time gas strategy.
    """

    duration = 30

    def __init__(self, time_duration: int = 30) -> None:
        self.duration = time_duration

    def interval(self) -> int:
        return int(time.time())

    @abstractmethod
    def get_gas_price(self) -> Generator[int, None, None]:
        """
        Generator function to yield gas prices for a transaction.

        Returns
        -------
        int
            Gas price, given as an integer in wei.
        """
        raise NotImplementedError
