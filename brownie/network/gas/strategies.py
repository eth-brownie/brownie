import threading
import time
from typing import Dict, Optional

import requests

from .bases import BlockGasStrategy, SimpleGasStrategy

_gasnow_update = 0
_gasnow_data: Dict[str, int] = {}
_gasnow_lock = threading.Lock()


def _fetch_gasnow(key: str) -> int:
    global _gasnow_update
    with _gasnow_lock:
        if time.time() - _gasnow_update > 15:
            data = None
            for i in range(12):
                response = requests.get(
                    "https://www.gasnow.org/api/v3/gas/price?utm_source=brownie"
                )
                if response.status_code != 200:
                    time.sleep(5)
                    continue
                data = response.json()["data"]
            if data is None:
                raise ValueError
            _gasnow_update = data.pop("timestamp") // 1000
            _gasnow_data.update(data)

    return _gasnow_data[key]


class GasNowStrategy(SimpleGasStrategy):
    def __init__(self, speed: str = "fast"):
        if speed not in ("rapid", "fast", "standard", "slow"):
            raise ValueError("`speed` must be one of: rapid, fast, standard, slow")
        self.speed = speed

    def get_gas_price(self) -> int:
        return _fetch_gasnow(self.speed)


class GasNowScalingStrategy(BlockGasStrategy):
    def __init__(
        self, initial_speed: str = "standard", increment: float = 1.1, block_duration: int = 2
    ):
        super().__init__(block_duration)
        if initial_speed not in ("rapid", "fast", "standard", "slow"):
            raise ValueError("`initial_speed` must be one of: rapid, fast, standard, slow")
        self.speed = initial_speed
        self.increment = increment

    def update_gas_price(self, last_gas_price: int, elapsed_blocks: int) -> Optional[int]:
        rapid_gas_price = _fetch_gasnow("rapid")
        new_gas_price = max(int(last_gas_price * self.increment), _fetch_gasnow(self.speed))
        if new_gas_price <= rapid_gas_price:
            return new_gas_price
        return None

    def get_gas_price(self) -> int:
        return _fetch_gasnow(self.speed)
