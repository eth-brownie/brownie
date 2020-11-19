import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from typing import Any

from brownie.network.web3 import web3


class GasABC(ABC):
    """
    Base ABC for all gas strategies.

    This class should not be directly subclassed from. Instead, use
    `SimpleGasStrategy`, `BlockGasStrategy` or `TimeGasStrategy`.
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


class SimpleGasStrategy(GasABC):
    """
    Abstract base class for simple gas strategies.

    Simple gas strategies are called once to provide a gas price
    at the time a transaction is broadcasted. Transactions using simple
    gas strategies are not automatically rebroadcasted.

    Subclass from this ABC to implement your own simple gas strategy.
    """


class BlockGasStrategy(GasABC):
    """
    Abstract base class for block gas strategies.

    Block gas strategies are called every `block_duration` blocks and
    can be used to automatically rebroadcast a pending transaction with
    a higher gas price.

    Subclass from this ABC to implement your own block gas strategy.
    """

    block_duration = 2

    def __init__(self, block_duration: int = 2) -> None:
        self.block_duration = block_duration

    @abstractmethod
    def update_gas_price(self, last_gas_price: int, elapsed_blocks: int) -> int:
        """
        Return an updated gas price.

        This method is called every `block_duration` blocks while a transaction
        is still pending. If the return value is at least 10% higher than the
        current gas price, the transaction is rebroadcasted with the new gas price.

        Arguments
        ---------
        last_gas_price : int
            The gas price of the most recently broadcasted transaction.
        elapsed_blocks : int
            The total number of blocks that have been mined since the first
            transaction using this strategy was broadcasted.

        Returns
        -------
        int, optional
            New gas price to rebroadcast the transaction with.
        """
        raise NotImplementedError


class TimeGasStrategy(GasABC):
    """
    Abstract base class for time gas strategies.

    Time gas strategies are called every `time_duration` seconds and
    can be used to automatically rebroadcast a pending transaction with
    a higher gas price.

    Subclass from this ABC to implement your own time gas strategy.
    """

    time_duration = 30

    def __init__(self, time_duration: int = 30) -> None:
        self.time_duration = time_duration

    @abstractmethod
    def update_gas_price(self, last_gas_price: int, elapsed_time: int) -> int:
        """
        Return an updated gas price.

        This method is called every `time_duration` seconds while a transaction
        is still pending. If the return value is at least 10% higher than the
        current gas price, the transaction is rebroadcasted with the new gas price.

        Arguments
        ---------
        last_gas_price : int
            The gas price of the most recently broadcasted transaction.
        elapsed_time : int
            The number of seconds that have passed since the first
            transaction using this strategy was broadcasted.

        Returns
        -------
        int, optional
            New gas price to rebroadcast the transaction with.
        """
        raise NotImplementedError


def _update_loop() -> None:
    while True:
        if not _queue:
            _event.wait()
            _event.clear()

        try:
            gas_strategy, tx, initial, latest = _queue.popleft()
        except IndexError:
            continue

        if tx.status >= 0:
            continue

        if isinstance(gas_strategy, BlockGasStrategy):
            height = web3.eth.blockNumber
            if height - latest >= gas_strategy.block_duration:
                gas_price = gas_strategy.update_gas_price(tx.gas_price, height - initial)
                if gas_price >= int(tx.gas_price * 1.1):
                    try:
                        tx = tx.replace(gas_price=gas_price)
                        latest = web3.eth.blockNumber
                    except ValueError:
                        pass

        elif isinstance(gas_strategy, TimeGasStrategy):
            if time.time() - latest >= gas_strategy.time_duration:
                gas_price = gas_strategy.update_gas_price(tx.gas_price, time.time() - initial)
                if gas_price >= int(tx.gas_price * 1.1):
                    try:
                        tx = tx.replace(gas_price=gas_price)
                        latest = time.time()
                    except ValueError:
                        pass

        _queue.append((gas_strategy, tx, initial, latest))
        time.sleep(1)


def _add_to_gas_strategy_queue(gas_strategy: GasABC, txreceipt: Any) -> None:
    if isinstance(gas_strategy, SimpleGasStrategy):
        return

    number = web3.eth.blockNumber if isinstance(gas_strategy, BlockGasStrategy) else time.time()
    _queue.append((gas_strategy, txreceipt, number, number))
    _event.set()


_queue: deque = deque()
_event = threading.Event()

_repricing_thread = threading.Thread(target=_update_loop, daemon=True)
_repricing_thread.start()
