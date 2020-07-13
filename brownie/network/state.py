#!/usr/bin/python3

import gc
import threading
import time
import weakref
from hashlib import sha1
from sqlite3 import OperationalError
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from brownie._config import CONFIG, _get_data_folder
from brownie._singleton import _Singleton
from brownie.exceptions import BrownieEnvironmentError, RPCRequestError
from brownie.project.build import DEPLOYMENT_KEYS
from brownie.utils.sql import Cursor

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
        return str(self._list)

    def __bool__(self) -> bool:
        return bool(self._list)

    def __contains__(self, item: Any) -> bool:
        return item in self._list

    def __iter__(self) -> Iterator:
        return iter(self._list)

    def __getitem__(self, key: Any) -> Any:
        return self._list[key]

    def __len__(self) -> int:
        return len(self._list)

    def _reset(self) -> None:
        self._list.clear()

    def _revert(self, height: int) -> None:
        self._list = [i for i in self._list if i.block_number <= height]

    def _add_tx(self, tx: Any) -> None:
        self._list.append(tx)

    def clear(self) -> None:
        self._list.clear()

    def copy(self) -> List:
        """Returns a shallow copy of the object as a list"""
        return self._list.copy()

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
    def __init__(self) -> None:
        self._time_offset: int = 0
        self._snapshot_id: Union[int, Optional[bool]] = False
        self._reset_id: Union[int, bool] = False
        self._current_id: Union[int, bool] = False
        self._undo_lock = threading.Lock()
        self._undo_buffer: List = []
        self._redo_buffer: List = []
        self._block_cache: Dict = {}

    def __len__(self) -> int:
        return web3.eth.blockNumber + 1

    def __getitem__(self, key):
        if not isinstance(key, int):
            raise
        if key < 0:
            key = web3.eth.blockNumber + 1 - key
        return web3.eth.getBlock(key)

    def _request(self, method: str, args: List) -> int:
        try:
            response = web3.provider.make_request(method, args)  # type: ignore
            if "result" in response:
                return response["result"]
        except AttributeError:
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

    def undo(self, num: int = 1) -> str:
        """
        Undo one or more transactions.

        Arguments
        ---------
        num : int, optional
            Number of transactions to undo.
        """
        with self._undo_lock:
            if num < 1:
                raise ValueError("num must be greater than zero")
            if not self._undo_buffer:
                raise ValueError("Undo buffer is empty")
            if num > len(self._undo_buffer):
                raise ValueError(f"Undo buffer contains {len(self._undo_buffer)} items")

            for i in range(num, 0, -1):
                id_, fn, args, kwargs = self._undo_buffer.pop()
                self._redo_buffer.append((fn, args, kwargs))

            self._current_id = self._revert(id_)
            return f"Block height at {web3.eth.blockNumber}"

    def redo(self, num: int = 1) -> str:
        """
        Redo one or more undone transactions.

        Arguments
        ---------
        num : int, optional
            Number of transactions to redo.
        """
        with self._undo_lock:
            if num < 1:
                raise ValueError("num must be greater than zero")
            if not self._redo_buffer:
                raise ValueError("Redo buffer is empty")
            if num > len(self._redo_buffer):
                raise ValueError(f"Redo buffer contains {len(self._redo_buffer)} items")

            for i in range(num, 0, -1):
                fn, args, kwargs = self._redo_buffer[-1]
                fn(*args, **kwargs)

            return f"Block height at {web3.eth.blockNumber}"

    def time(self) -> int:
        """Returns the current epoch time from the test RPC as an int"""
        return int(time.time() + self._time_offset)

    def sleep(self, seconds: int) -> None:
        """Increases the time within the test RPC.

        Args:
            seconds (int): Number of seconds to increase the time by."""
        if not isinstance(seconds, int):
            raise TypeError("seconds must be an integer value")
        self._time_offset = self._request("evm_increaseTime", [seconds])

        if seconds:
            self._redo_buffer.clear()
            self._current_id = self._snap()

    def mine(self, blocks: int = 1) -> str:
        """Increases the block height within the test RPC.

        Args:
            blocks (int): Number of new blocks to be mined."""
        if not isinstance(blocks, int):
            raise TypeError("blocks must be an integer value")
        for i in range(blocks):
            self._request("evm_mine", [])

        self._redo_buffer.clear()
        self._current_id = self._snap()
        return f"Block height at {web3.eth.blockNumber}"

    def snapshot(self) -> str:
        """
        Take a snapshot of the current state of the EVM.

        This action clears the undo buffer.
        """
        self._undo_buffer.clear()
        self._redo_buffer.clear()
        self._snapshot_id = self._current_id = self._snap()
        return f"Snapshot taken at block height {web3.eth.blockNumber}"

    def revert(self) -> str:
        """
        Revert the EVM to the most recently taken snapshot.

        This action clears the undo buffer.
        """
        if not self._snapshot_id:
            raise ValueError("No snapshot set")
        self._undo_buffer.clear()
        self._redo_buffer.clear()
        self._snapshot_id = self._current_id = self._revert(self._snapshot_id)
        return f"Block height reverted to {web3.eth.blockNumber}"

    def reset(self) -> None:
        """
        Revert the EVM to the initial state when loaded.

        This action clears the undo buffer.
        """
        self._snapshot_id = None
        self._undo_buffer.clear()
        self._redo_buffer.clear()
        self._reset_id = self._current_id = self._revert(self._reset_id)

    def _network_reset(self) -> None:
        try:
            self.reset()
        except RPCRequestError:
            self._reset_id = self._current_id = False
            _notify_registry(0)


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
