from abc import ABC, abstractmethod
from typing import Optional


class GasABC(ABC):
    pass


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
