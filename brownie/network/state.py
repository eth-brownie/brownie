#!/usr/bin/python3

import gc
import threading
import time
import weakref
from hashlib import sha1
from sqlite3 import OperationalError
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union

from hexbytes import HexBytes
from requests.exceptions import ConnectionError as RequestsConnectionError
from web3.types import BlockData

from brownie._config import CONFIG, _get_data_folder
from brownie._singleton import _Singleton
from brownie.convert import Wei
from brownie.exceptions import BrownieEnvironmentError, RPCRequestError
from brownie.project.build import DEPLOYMENT_KEYS
from brownie.utils.sql import Cursor

from .transaction import TransactionReceipt
from .web3 import _resolve_address, web3

_contract_map: Dict = {}
_revert_refs: List = []

cur = Cursor(_get_data_folder().joinpath("deployments.db"))
cur.execute("CREATE TABLE IF NOT EXISTS sources (hash PRIMARY KEY, source)")


class TxHistory(metaclass=_Singleton):

    """List-like singleton container that contains TransactionReceipt objects.
    Whenever a transaction is broadcast, the TransactionReceipt is automatically
    added to this container."""

    def __init__(self) -> None:
        self._list: List = []
        self.gas_profile: Dict = {}
        _revert_register(self)

    def __repr__(self) -> str:
        if CONFIG.argv["cli"] == "console":
            return str(self._list)
        return super().__repr__()

    def __bool__(self) -> bool:
        return bool(self._list)

    def __contains__(self, item: Any) -> bool:
        return item in self._list

    def __iter__(self) -> Iterator:
        return iter(self._list)

    def __getitem__(self, key: int) -> TransactionReceipt:
        return self._list[key]

    def __len__(self) -> int:
        return len(self._list)

    def _reset(self) -> None:
        self._list.clear()

    def _revert(self, height: int) -> None:
        self._list = [i for i in self._list if i.block_number <= height]

    def _add_tx(self, tx: TransactionReceipt) -> None:
        self._list.append(tx)

    def clear(self) -> None:
        self._list.clear()

    def copy(self) -> List:
        """Returns a shallow copy of the object as a list"""
        return self._list.copy()

    def filter(self, key: Optional[Callable] = None, **kwargs: Dict) -> List:
        """
        Return a filtered list of transactions.

        Arguments
        ---------
        key : Callable, optional
            An optional function to filter with. It should expect one agument and return
            True or False.

        Keyword Arguments
        -----------------
        **kwargs : Any
            Names and expected values for TransactionReceipt attributes.

        Returns
        -------
        List
            A filtered list of TransactionReceipt objects.
        """
        result = [i for i in self._list if all(getattr(i, k) == v for k, v in kwargs.items())]
        if key is None:
            return result
        return [i for i in result if key(i)]

    def from_sender(self, account: str) -> List:
        """Returns a list of transactions where the sender is account"""
        return [i for i in self._list if i.sender == account]

    def to_receiver(self, account: str) -> List:
        """Returns a list of transactions where the receiver is account"""
        return [i for i in self._list if i.receiver == account]

    def of_address(self, account: str) -> List:
        """Returns a list of transactions where account is the sender or receiver"""
        return [i for i in self._list if i.receiver == account or i.sender == account]

    def _gas(self, fn_name: str, gas_used: int) -> None:
        if fn_name not in self.gas_profile:
            self.gas_profile[fn_name] = {
                "avg": gas_used,
                "high": gas_used,
                "low": gas_used,
                "count": 1,
            }
            return
        gas = self.gas_profile[fn_name]
        gas.update(
            {
                "avg": (gas["avg"] * gas["count"] + gas_used) // (gas["count"] + 1),
                "high": max(gas["high"], gas_used),
                "low": min(gas["low"], gas_used),
            }
        )
        gas["count"] += 1


class Chain(metaclass=_Singleton):

    """
    List-like singleton used to access block data, and perform actions such as
    snapshotting, mining, and chain rewinds.
    """

    def __init__(self) -> None:
        self._time_offset: int = 0
        self._snapshot_id: Optional[int] = None
        self._reset_id: Optional[int] = None
        self._current_id: Optional[int] = None
        self._undo_lock = threading.Lock()
        self._undo_buffer: List = []
        self._redo_buffer: List = []
        self._chainid: Optional[int] = None
        self._block_gas_time: int = -1
        self._block_gas_limit: int = 0

    def __repr__(self) -> str:
        try:
            return f"<Chain object (chainid={self.id}, height={self.height})>"
        except Exception:
            return "<Chain object (disconnected)>"

    def __len__(self) -> int:
        """
        Return the current number of blocks.
        """
        return web3.eth.blockNumber + 1

    def __getitem__(self, block_number: int) -> BlockData:
        """
        Return information about a block by block number.

        Arguments
        ---------
        block_number : int
            Integer of a block number. If the value is negative, the block returned
            is relative to the most recently mined block, e.g. `chain[-1]` returns
            the most recent block.

        Returns
        -------
        BlockData
            web3 block data object
        """
        if not isinstance(block_number, int):
            raise TypeError("Block height must be given as an integer")
        if block_number < 0:
            block_number = web3.eth.blockNumber + 1 + block_number
        block = web3.eth.getBlock(block_number)
        if block["timestamp"] > self._block_gas_time:
            self._block_gas_limit = block["gasLimit"]
            self._block_gas_time = block["timestamp"]
        return block

    def new_blocks(self, height_buffer: int = 0, poll_interval: int = 5) -> Iterator:
        """
        Generator for iterating over new blocks.

        Arguments
        ---------
        height_buffer : int, optional
            The number of blocks behind "latest" to return. A higher value means
            more delayed results but less likelihood of uncles.
        poll_interval : int, optional
            Maximum interval between querying for a new block, if the height has
            not changed. Set this lower to detect uncles more frequently.
        """
        if height_buffer < 0:
            raise ValueError("Buffer cannot be negative")

        last_block = None
        last_height = 0
        last_poll = 0.0

        while True:
            if last_poll + poll_interval < time.time() or last_height != web3.eth.blockNumber:
                last_height = web3.eth.blockNumber
                block = web3.eth.getBlock(last_height - height_buffer)
                last_poll = time.time()

                if block != last_block:
                    last_block = block
                    yield last_block
            else:
                time.sleep(1)

    @property
    def height(self) -> int:
        return web3.eth.blockNumber

    @property
    def id(self) -> int:
        if self._chainid is None:
            self._chainid = web3.eth.chainId
        return self._chainid

    @property
    def block_gas_limit(self) -> Wei:
        if time.time() > self._block_gas_time + 3600:
            block = web3.eth.getBlock("latest")
            self._block_gas_limit = block["gasLimit"]
            self._block_gas_time = block["timestamp"]
        return Wei(self._block_gas_limit)

    def _request(self, method: str, args: List) -> int:
        try:
            response = web3.provider.make_request(method, args)  # type: ignore
            if "result" in response:
                return response["result"]
        except (AttributeError, RequestsConnectionError):
            raise RPCRequestError("Web3 is not connected.")
        raise RPCRequestError(response["error"]["message"])

    def _snap(self) -> int:
        return self._request("evm_snapshot", [])

    def _revert(self, id_: int) -> int:
        if web3.isConnected() and not web3.eth.blockNumber and not self._time_offset:
            _notify_registry(0)
            return self._snap()
        self._request("evm_revert", [id_])
        id_ = self._snap()
        self.sleep(0)
        _notify_registry()
        return id_

    def _add_to_undo_buffer(self, tx: Any, fn: Any, args: Tuple, kwargs: Dict) -> None:
        with self._undo_lock:
            tx._confirmed.wait()
            self._undo_buffer.append((self._current_id, fn, args, kwargs))
            if self._redo_buffer and (fn, args, kwargs) == self._redo_buffer[-1]:
                self._redo_buffer.pop()
            else:
                self._redo_buffer.clear()
            self._current_id = self._snap()

    def _network_connected(self) -> None:
        self._reset_id = None
        self.reset()

    def _network_disconnected(self) -> None:
        self._undo_buffer.clear()
        self._redo_buffer.clear()
        self._snapshot_id = None
        self._reset_id = None
        self._current_id = None
        self._chainid = None
        _notify_registry(0)

    def get_transaction(self, txid: Union[str, bytes]) -> TransactionReceipt:
        """
        Return a TransactionReceipt object for the given transaction hash.
        """
        if not isinstance(txid, str):
            txid = HexBytes(txid).hex()
        tx = next((i for i in TxHistory() if i.txid == txid), None)
        return tx or TransactionReceipt(txid, silent=True, required_confs=0)

    def time(self) -> int:
        """Return the current epoch time from the test RPC as an int"""
        return int(time.time() + self._time_offset)

    def sleep(self, seconds: int) -> None:
        """
        Increase the time within the test RPC.

        Arguments
        ---------
        seconds : int
            Number of seconds to increase the time by
        """
        if not isinstance(seconds, int):
            raise TypeError("seconds must be an integer value")
        self._time_offset = self._request("evm_increaseTime", [seconds])

        if seconds:
            self._redo_buffer.clear()
            self._current_id = self._snap()

    def mine(self, blocks: int = 1) -> int:
        """
        Increase the block height within the test RPC.

        Arguments
        ---------
        blocks : int
            Number of new blocks to be mined

        Returns
        -------
        int
            Current block height
        """
        if not isinstance(blocks, int):
            raise TypeError("blocks must be an integer value")
        for i in range(blocks):
            self._request("evm_mine", [])

        self._redo_buffer.clear()
        self._current_id = self._snap()
        return web3.eth.blockNumber

    def snapshot(self) -> None:
        """
        Take a snapshot of the current state of the EVM.

        This action clears the undo buffer.
        """
        self._undo_buffer.clear()
        self._redo_buffer.clear()
        self._snapshot_id = self._current_id = self._snap()

    def revert(self) -> int:
        """
        Revert the EVM to the most recently taken snapshot.

        This action clears the undo buffer.

        Returns
        -------
        int
            Current block height
        """
        if self._snapshot_id is None:
            raise ValueError("No snapshot set")
        self._undo_buffer.clear()
        self._redo_buffer.clear()
        self._snapshot_id = self._current_id = self._revert(self._snapshot_id)
        return web3.eth.blockNumber

    def reset(self) -> int:
        """
        Revert the EVM to the initial state when loaded.

        This action clears the undo buffer.

        Returns
        -------
        int
            Current block height
        """
        self._snapshot_id = None
        self._undo_buffer.clear()
        self._redo_buffer.clear()
        if self._reset_id is None:
            self._reset_id = self._current_id = self._snap()
            _notify_registry(0)
        else:
            self._reset_id = self._current_id = self._revert(self._reset_id)
        return web3.eth.blockNumber

    def undo(self, num: int = 1) -> int:
        """
        Undo one or more transactions.

        Arguments
        ---------
        num : int, optional
            Number of transactions to undo.

        Returns
        -------
        int
            Current block height
        """
        with self._undo_lock:
            if num < 1:
                raise ValueError("num must be greater than zero")
            if not self._undo_buffer:
                raise ValueError("Undo buffer is empty")
            if num > len(self._undo_buffer):
                raise ValueError(f"Undo buffer contains {len(self._undo_buffer)} items")

            for i in range(num):
                id_, fn, args, kwargs = self._undo_buffer.pop()
                self._redo_buffer.append((fn, args, kwargs))

            self._current_id = self._revert(id_)
            return web3.eth.blockNumber

    def redo(self, num: int = 1) -> int:
        """
        Redo one or more undone transactions.

        Arguments
        ---------
        num : int, optional
            Number of transactions to redo.

        Returns
        -------
        int
            Current block height
        """
        with self._undo_lock:
            if num < 1:
                raise ValueError("num must be greater than zero")
            if not self._redo_buffer:
                raise ValueError("Redo buffer is empty")
            if num > len(self._redo_buffer):
                raise ValueError(f"Redo buffer contains {len(self._redo_buffer)} items")

            for i in range(num):
                fn, args, kwargs = self._redo_buffer.pop()
                fn(*args, **kwargs)

            return web3.eth.blockNumber


# objects that will update whenever the RPC is reset or reverted must register
# by calling to this function. The must also include _revert and _reset methods
# to recieve notifications from this object
def _revert_register(obj: object) -> None:
    _revert_refs.append(weakref.ref(obj))


def _notify_registry(height: int = None) -> None:
    gc.collect()
    if height is None:
        height = web3.eth.blockNumber
    for ref in _revert_refs.copy():
        obj = ref()
        if obj is None:
            _revert_refs.remove(ref)
        elif height:
            obj._revert(height)
        else:
            obj._reset()


def _find_contract(address: Any) -> Any:
    if address is None:
        return

    address = _resolve_address(address)
    if address in _contract_map:
        return _contract_map[address]
    if "chainid" in CONFIG.active_network:
        try:
            from brownie.network.contract import Contract

            return Contract(address)
        except ValueError:
            pass


def _get_current_dependencies() -> List:
    dependencies = set(v._name for v in _contract_map.values())
    for contract in _contract_map.values():
        dependencies.update(contract._build.get("dependencies", []))
    return sorted(dependencies)


def _add_contract(contract: Any) -> None:
    _contract_map[contract.address] = contract


def _remove_contract(contract: Any) -> None:
    del _contract_map[contract.address]


def _get_deployment(
    address: str = None, alias: str = None
) -> Tuple[Optional[Dict], Optional[Dict]]:
    if address and alias:
        raise
    if address:
        address = _resolve_address(address)
        query = f"address='{address}'"
    elif alias:
        query = f"alias='{alias}'"

    try:
        name = f"chain{CONFIG.active_network['chainid']}"
    except KeyError:
        raise BrownieEnvironmentError("Functionality not available in local environment") from None
    try:
        row = cur.fetchone(f"SELECT * FROM {name} WHERE {query}")
    except OperationalError:
        row = None
    if not row:
        return None, None

    keys = ["address", "alias", "paths"] + DEPLOYMENT_KEYS
    build_json = {k: v for k, v in zip(keys, row)}
    path_map = build_json.pop("paths")
    sources = {
        i[1]: cur.fetchone("SELECT source FROM sources WHERE hash=?", (i[0],))[0]
        for i in path_map.values()
    }
    build_json["allSourcePaths"] = {k: v[1] for k, v in path_map.items()}
    if isinstance(build_json["pcMap"], dict):
        build_json["pcMap"] = dict((int(k), v) for k, v in build_json["pcMap"].items())

    return build_json, sources


def _add_deployment(contract: Any, alias: Optional[str] = None) -> None:
    if "chainid" not in CONFIG.active_network:
        return

    address = _resolve_address(contract.address)
    name = f"chain{CONFIG.active_network['chainid']}"

    cur.execute(
        f"CREATE TABLE IF NOT EXISTS {name} "
        f"(address UNIQUE, alias UNIQUE, paths, {', '.join(DEPLOYMENT_KEYS)})"
    )

    all_sources = {}
    for key, path in contract._build.get("allSourcePaths", {}).items():
        source = contract._sources.get(path)
        hash_ = sha1(source.encode()).hexdigest()
        cur.insert("sources", hash_, source)
        all_sources[key] = [hash_, path]

    values = [contract._build.get(i) for i in DEPLOYMENT_KEYS]
    cur.insert(name, address, alias, all_sources, *values)
