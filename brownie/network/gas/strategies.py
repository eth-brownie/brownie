import threading
import time

import requests

from .bases import BlockGasStrategy, SimpleGasStrategy

_gasnow = {"time": 0, "data": None}
_gasnow_lock = threading.Lock()


def _fetch_gasnow(key):
    with _gasnow_lock:
        if time.time() - _gasnow["time"] > 15:
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
            _gasnow["time"] = data.pop("timestamp") // 1000
            _gasnow["data"] = data

    return _gasnow["data"][key]


class GasNowStrategy(SimpleGasStrategy):
    def __init__(self, speed: str = "fast"):
        if speed not in ("rapid", "fast", "standard", "slow"):
            raise ValueError("`speed` must be one of: rapid, fast, standard, slow")
        self.speed = speed

    def get_gas_price(self):
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

    def get_gas_price(self, current_gas_price, elapsed_blocks):
        if current_gas_price is None:
            return _fetch_gasnow(self.speed)
        rapid_gas_price = _fetch_gasnow("rapid")
        new_gas_price = max(int(current_gas_price * self.increment), _fetch_gasnow(self.speed))
        if new_gas_price <= rapid_gas_price:
            return new_gas_price
        return None
