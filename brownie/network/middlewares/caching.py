import hexbytes
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Dict, Final, List, Optional, final

from web3 import Web3
from web3.types import LogReceipt

from brownie._c_constants import HexBytes, json_dumps
from brownie._config import CONFIG, _get_data_folder
from brownie.network.middlewares import BrownieMiddlewareABC
from brownie.utils.sql import Cursor

# calls to the following RPC endpoints are stored in a persistent cache
# if the returned data evaluates true when passed into the lambda
LONGTERM_CACHE: Final = {
    "eth_getCode": lambda w3, data: is_cacheable_bytecode(w3, data),
}


def _strip_push_data(bytecode: bytes) -> bytes:
    idx = 0
    while idx < len(bytecode):
        # if instruction is between PUSH1 and PUSH32
        if 0x60 <= bytecode[idx] <= 0x7F:
            offset = idx + 1
            length = bytecode[idx] - 0x5F
            bytecode = bytecode[:offset] + bytecode[offset + length :]
        idx += 1
    return bytecode


def is_cacheable_bytecode(web3: Web3, bytecode: hexbytes.HexBytes) -> bool:
    """
    Check if bytecode can safely by cached.

    To safely cache bytecode we verify that the code cannot be removed via a
    SELFDESTRUCT operation, or a SELFDESTRUCT triggered via a DELEGATECALL.

    Arguments
    ---------
    web3 : Web3
        Web3 object connected to the same network that the bytecode exists on.
    bytecode : HexBytes
        Deployed bytecode to be analyzed.

    Returns
    -------
    bool
        Can this bytecode be cached?
    """
    if not bytecode:
        # do not cache empty code, something might be deployed there later!
        return False

    bytecode_bytes = bytes(HexBytes(bytecode))
    opcodes = _strip_push_data(bytecode_bytes)
    if 0xFF in opcodes:
        # cannot cache if the code contains a SELFDESTRUCT instruction
        return False
    for idx in [i for i in range(len(opcodes)) if opcodes[i] == 0xF4]:
        # cannot cache if the code performs a DELEGATECALL to a not-fixed address
        if idx < 2:
            return False
        if opcodes[idx - 2 : idx] != b"sZ":  # b"sZ" == bytes(HexBytes("0x735A"))
            # if the instruction not is immediately preceded by PUSH20 GAS
            # the target was not hardcoded and we cannot cache
            return False

    # check if the target code of each delegatecall is also cachable
    # if yes then we can cache this contract as well
    push20_indexes = (
        i for i in range(len(bytecode_bytes) - 22)
        if bytecode_bytes[i] == 0x73 and bytecode_bytes[i + 22] == 0xF4
    )
    for address in (bytecode_bytes[i + 1 : i + 21] for i in push20_indexes):
        if not int(address.hex(), 16):
            # if the delegatecall targets 0x00 this is a factory pattern, we can ignore
            continue
        target_bytecode = web3.eth.get_code(address)
        if not is_cacheable_bytecode(web3, target_bytecode):
            return False

    return True


def _new_filter(w3: Web3) -> Any:
    # returns a filter if the client is connected and supports filtering
    try:
        block_filter = w3.eth.filter("latest")
        block_filter.get_new_entries()
        return block_filter
    except (AttributeError, ValueError):
        return None


@final
class RequestCachingMiddleware(BrownieMiddlewareABC):
    """
    Web3 middleware for request caching.
    """

    def __init__(self, w3: Web3) -> None:
        super().__init__(w3)

        self.table_key: Final = f"chain{CONFIG.active_network['chainid']}"
        self.cur: Final = Cursor(_get_data_folder().joinpath("cache.db"))
        self.cur.execute(f"CREATE TABLE IF NOT EXISTS {self.table_key} (method, params, result)")

        self.lock: Final = threading.Lock()
        self.event: Final = threading.Event()
        self.start_block_filter_loop()

    def start_block_filter_loop(self):
        self.event.clear()
        self.loop_thread = threading.Thread(target=self.loop_exception_handler, daemon=True)
        self.loop_thread.start()
        self.event.wait()

    @classmethod
    def get_layer(cls, w3: Web3, network_type: str) -> Optional[int]:
        if CONFIG.settings["eager_caching"] is False:
            # do not cache when user doesn't want it
            return None
        if network_type != "live":
            # do not cache on development chains
            return None
        try:
            latest = w3.eth.get_block("latest")
        except Exception:
            return None
        if latest.timestamp - w3.eth.get_block(latest.number - 50).timestamp < 250:
            # do not cache on chains with an average block time of less than 5 seconds
            return None
        if _new_filter(w3) is None:
            # do not cache if we cannot create a filter for new blocks
            return None
        return 0

    @property
    def time_since(self) -> float:
        return time.time() - self.last_request

    def loop_exception_handler(self) -> None:
        try:
            self.block_filter_loop()
        except Exception:
            # catch unhandled exceptions to avoid random error messages in the console
            self.block_cache.clear()
            self.is_killed = True

    def block_filter_loop(self) -> None:
        # initialize required state variables within the loop to avoid recursion death
        latest = self.w3.eth.get_block("latest")
        self.last_block = latest.hash
        self.last_block_seen = latest.timestamp
        self.last_request = time.time()
        self.block_cache: OrderedDict = OrderedDict()
        self.block_filter = self.w3.eth.filter("latest")
        self.is_killed = False
        self.event.set()

        new_blocks: List[LogReceipt]
        while not self.is_killed:
            # if the last RPC request was > 60 seconds ago, reduce the rate of updates.
            # we eventually settle at one query per minute after 10 minutes of no requests.
            with self.lock:
                if self.time_since > 60:
                    self.block_cache.clear()
                    self.event.clear()
            if self.time_since > 60:
                self.event.wait(min(self.time_since / 10, 60))

            # query the filter for new blocks
            with self.lock:
                try:
                    new_blocks = self.block_filter.get_new_entries()
                except (AttributeError, ValueError):
                    # web3 has disconnected, or the filter has expired from inactivity
                    # some public nodes allow a filter initially, but block it several seconds later
                    block_filter = _new_filter(self.w3)
                    if block_filter is None:
                        return
                    self.block_filter = block_filter

                    # continue in try: except: block is not supported by mypyc
                    # as of jul 23 2025 so we use this workaround instead.
                    should_skip = True
                else:
                    should_skip = False
                    if new_blocks:
                        self.block_cache[new_blocks[-1]] = {}
                        self.last_block = new_blocks[-1]
                        self.last_block_seen = time.time()
                        if len(self.block_cache) > 5:
                            old_key = list(self.block_cache)[0]
                            del self.block_cache[old_key]

            # continue in try: except: block is not supported by mypyc
            # as of jul 23 2025 so we use this workaround instead.
            if should_skip:
                pass

            elif new_blocks and self.time_since < 15:
                # if this update found a new block and we've been querying
                # frequently, we can wait a few seconds before the next update
                time.sleep(5)
            elif time.time() - self.last_block_seen < 15:
                # if it's been less than 15 seconds since the last block, wait 2 seconds
                time.sleep(2)
            else:
                # if it's been more than 15 seconds, only wait 1 second
                time.sleep(1)

    def process_request(self, make_request: Callable, method: str, params: List) -> Dict:
        if method in (
            # caching any of these means we die of recursion death so let's not do that
            "eth_getFilterChanges",
            "eth_newBlockFilter",
            "eth_uninstallFilter",
            # used to check connectivity
            "web3_clientVersion",
            # caching these causes weirdness with transaction broadcasting and replacement
            "eth_sendTransaction",
            "eth_sendRawTransaction",
            "eth_sign",
            "eth_signTransaction",
            "eth_getTransactionByHash",
            "eth_getTransactionReceipt",
            "eth_chainId",
        ):
            return make_request(method, params)

        # try to return a cached value
        param_str = json_dumps(params, separators=(",", ""), default=str)

        # check if the value is available within the long-term cache
        if method in LONGTERM_CACHE:
            row = self.cur.fetchone(
                f"SELECT result FROM {self.table_key} WHERE method=? AND params=?",
                (method, param_str),
            )
            if row:
                data = row[0]
                if isinstance(data, bytes):
                    data = HexBytes(data)
                return {"id": "cache", "jsonrpc": "2.0", "result": data}

        if not self.loop_thread.is_alive():
            # restart the block filter loop if it has crashed (usually from a ConnectionError)
            self.start_block_filter_loop()

        with self.lock:
            self.last_request = time.time()
            self.event.set()
            try:
                return self.block_cache[self.last_block][method][param_str]
            except KeyError:
                pass

        # cached value is unavailable, make a request and cache the result
        with self.lock:
            response = make_request(method, params)
            self.block_cache.setdefault(self.last_block, {}).setdefault(method, {})
            self.block_cache[self.last_block][method][param_str] = response

        # check if the value can be added to long-term cache
        if "result" in response and method in LONGTERM_CACHE:
            result = response["result"]
            if LONGTERM_CACHE[method](self.w3, result):
                if isinstance(result, (dict, list, tuple)):
                    result = json_dumps(response, separators=(",", ""), default=str)
                self.cur.insert(self.table_key, method, param_str, result)

        return response

    def uninstall(self) -> None:
        self.is_killed = True
        self.block_cache.clear()
        if self.w3.isConnected():
            self.w3.eth.uninstall_filter(self.block_filter.filter_id)
