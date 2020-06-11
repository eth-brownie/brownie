#!/usr/bin/python3

from hashlib import sha1
from sqlite3 import OperationalError
from typing import Any, Dict, Iterator, List, Optional, Tuple

from brownie._config import CONFIG, _get_data_folder
from brownie._singleton import _Singleton
from brownie.exceptions import BrownieEnvironmentError
from brownie.project.build import DEPLOYMENT_KEYS
from brownie.utils.sql import Cursor

from .rpc import _revert_register
from .web3 import _resolve_address

_contract_map: Dict = {}

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
