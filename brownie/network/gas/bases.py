import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from typing import Any, Optional

from brownie.network.web3 import web3


class GasABC(ABC):
    def _add_tx(self, txreceipt: Any) -> None:
        if isinstance(self, SimpleGasStrategy):
            return

        number = web3.eth.blockNumber if isinstance(self, BlockGasStrategy) else time.time()
        _queue.append((self, txreceipt, number, number))
        _event.set()


class SimpleGasStrategy(GasABC):
    @abstractmethod
    def get_gas_price(self) -> int:
        raise NotImplementedError


class BlockGasStrategy(GasABC):

    block_duration = 2

    def __init__(self, block_duration: int = 2):
        self.block_duration = block_duration

    @abstractmethod
    def get_gas_price(self, current_gas_price: int, elapsed_blocks: int) -> Optional[int]:
        raise NotImplementedError


class TimeGasStrategy(GasABC):

    time_duration = 30

    def __init__(self, time_duration: int = 30) -> None:
        self.time_duration = time_duration

    @abstractmethod
    def get_gas_price(self, current_gas_price: int, elapsed_time: int) -> Optional[int]:
        raise NotImplementedError


def _update_loop():
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
                gas_price = gas_strategy.get_gas_price(tx.gas_price, height - initial)
                if gas_price is not None:
                    tx = tx.replace(gas_price=gas_price, silent=True)
                    latest = web3.eth.blockNumber

        else:
            if time.time() - latest >= gas_strategy.time_duration:
                gas_price = gas_strategy.get_gas_price(tx.gas_price, time.time() - initial)
                if gas_price is not None:
                    tx = tx.replace(gas_price=gas_price, silent=True)
                    latest = time.time()

        _queue.append((gas_strategy, tx, initial, latest))
        time.sleep(1)


_queue: deque = deque()
_event = threading.Event()

_repricing_thread = threading.Thread(target=_update_loop, daemon=True)
_repricing_thread.start()
