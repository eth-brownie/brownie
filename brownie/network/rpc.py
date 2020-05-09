#!/usr/bin/python3

import atexit
import datetime
import gc
import sys
import threading
import time
import warnings
import weakref
from subprocess import DEVNULL, PIPE
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import psutil

from brownie._config import EVM_EQUIVALENTS
from brownie._singleton import _Singleton
from brownie.convert import Wei
from brownie.exceptions import (
    InvalidArgumentWarning,
    RPCConnectionError,
    RPCProcessError,
    RPCRequestError,
)

from .web3 import web3

CLI_FLAGS = {
    "port": "--port",
    "gas_limit": "--gasLimit",
    "accounts": "--accounts",
    "evm_version": "--hardfork",
    "fork": "--fork",
    "mnemonic": "--mnemonic",
    "account_keys_path": "--acctKeys",
    "block_time": "--blockTime",
    "default_balance": "--defaultBalanceEther",
    "time": "--time",
}

EVM_VERSIONS = ["byzantium", "constantinople", "petersburg", "istanbul"]
EVM_DEFAULT = "istanbul"

__tracebackhide__ = True
_revert_refs: List = []


class Rpc(metaclass=_Singleton):

    """Methods for interacting with ganache-cli when running a local
    RPC environment.

    Account balances, contract containers and transaction history are
    automatically modified when the RPC is terminated, reset or reverted."""

    def __init__(self) -> None:
        self._rpc: Any = None
        self._time_offset: int = 0
        self._snapshot_id: Union[int, Optional[bool]] = False
        self._reset_id: Union[int, bool] = False
        self._current_id: Union[int, bool] = False
        self._undo_lock = threading.Lock()
        self._undo_buffer: List = []
        self._redo_buffer: List = []
        atexit.register(self._at_exit)

    def _at_exit(self) -> None:
        if not self.is_active():
            return
        if self._rpc.parent() == psutil.Process():
            if getattr(self._rpc, "stdout", None) is not None:
                self._rpc.stdout.close()
            if getattr(self._rpc, "stderr", None) is not None:
                self._rpc.stderr.close()
            self.kill(False)
        else:
            self._request("evm_revert", [self._reset_id])

    def launch(self, cmd: str, **kwargs: Dict) -> None:
        """Launches the RPC client.

        Args:
            cmd: command string to execute as subprocess"""
        if self.is_active():
            raise SystemError("RPC is already active.")
        if sys.platform == "win32" and not cmd.split(" ")[0].endswith(".cmd"):
            if " " in cmd:
                cmd = cmd.replace(" ", ".cmd ", 1)
            else:
                cmd += ".cmd"
        kwargs.setdefault("evm_version", EVM_DEFAULT)  # type: ignore
        if kwargs["evm_version"] in EVM_EQUIVALENTS:
            kwargs["evm_version"] = EVM_EQUIVALENTS[kwargs["evm_version"]]  # type: ignore
        kwargs = _validate_cmd_settings(kwargs)
        for key, value in [(k, v) for k, v in kwargs.items() if v]:
            try:
                cmd += f" {CLI_FLAGS[key]} {value}"
            except KeyError:
                warnings.warn(
                    f"Ignoring invalid commandline setting for ganache-cli: "
                    f'"{key}" with value "{value}".',
                    InvalidArgumentWarning,
                )
        print(f"Launching '{cmd}'...")
        self._time_offset = 0
        self._snapshot_id = False
        self._reset_id = False
        out = DEVNULL if sys.platform == "win32" else PIPE
        self._rpc = psutil.Popen(cmd.split(" "), stdin=DEVNULL, stdout=out, stderr=out)
        # check that web3 can connect
        if not web3.provider:
            _notify_registry(0)
            return
        uri = web3.provider.endpoint_uri if web3.provider else None
        for i in range(100):
            if web3.isConnected():
                self._reset_id = self._current_id = self._snap()
                _notify_registry(0)
                self._time_offset = self._request("evm_increaseTime", [0])
                return
            time.sleep(0.1)
            if type(self._rpc) is psutil.Popen:
                self._rpc.poll()
            if not self._rpc.is_running():
                self.kill(False)
                raise RPCProcessError(cmd, uri)
        self.kill(False)
        raise RPCConnectionError(cmd, self._rpc, uri)

    def attach(self, laddr: Union[str, Tuple]) -> None:
        """Attaches to an already running RPC client subprocess.

        Args:
            laddr: Address that the client is listening at. Can be supplied as a
                   string "http://127.0.0.1:8545" or tuple ("127.0.0.1", 8545)"""
        if self.is_active():
            raise SystemError("RPC is already active.")
        if isinstance(laddr, str):
            o = urlparse(laddr)
            if not o.port:
                raise ValueError("No RPC port given")
            laddr = (o.hostname, o.port)
        try:
            proc = next(i for i in psutil.process_iter() if _check_connections(i, laddr))
        except StopIteration:
            raise ProcessLookupError(
                "Could not attach to RPC process. If this issue persists, try killing "
                "the RPC and let Brownie launch it as a child process."
            ) from None
        print(f"Attached to local RPC client listening at '{laddr[0]}:{laddr[1]}'...")
        self._rpc = psutil.Process(proc.pid)
        self._time_offset = self._request("evm_increaseTime", [0])
        if web3.provider:
            self._reset_id = self._current_id = self._snap()
        _notify_registry(0)

    def kill(self, exc: bool = True) -> None:
        """Terminates the RPC process and all children with SIGKILL.

        Args:
            exc: if True, raises SystemError if subprocess is not active."""
        if not self.is_active():
            if not exc:
                return
            raise SystemError("RPC is not active.")

        try:
            print("Terminating local RPC client...")
        except ValueError:
            pass
        for child in self._rpc.children():
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        self._rpc.kill()
        self._rpc.wait()
        self._time_offset = 0
        self._snapshot_id = False
        self._reset_id = False
        self._current_id = False
        self._undo_buffer.clear()
        self._redo_buffer.clear()
        self._rpc = None
        _notify_registry(0)

    def _request(self, method: str, args: List) -> int:
        if not self.is_active():
            raise SystemError("RPC is not active.")
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

    def is_active(self) -> bool:
        """Returns True if Rpc client is currently active."""
        if not self._rpc:
            return False
        if type(self._rpc) is psutil.Popen:
            self._rpc.poll()
        return self._rpc.is_running()

    def is_child(self) -> bool:
        """Returns True if the Rpc client is active and was launched by Brownie."""
        if not self.is_active():
            return False
        return self._rpc.parent() == psutil.Process()

    def evm_version(self) -> Optional[str]:
        """Returns the currently active EVM version."""
        if not self.is_active():
            return None
        cmd = self._rpc.cmdline()
        key = next((i for i in ("--hardfork", "-k") if i in cmd), None)
        try:
            return cmd[cmd.index(key) + 1]
        except (ValueError, IndexError):
            return EVM_DEFAULT

    def evm_compatible(self, version: str) -> bool:
        """Returns a boolean indicating if the given version is compatible with
        the currently active EVM version."""
        if not self.is_active():
            raise RPCRequestError("RPC is not active")
        version = EVM_EQUIVALENTS.get(version, version)
        try:
            return EVM_VERSIONS.index(version) <= EVM_VERSIONS.index(  # type: ignore
                self.evm_version()
            )
        except ValueError:
            raise ValueError(f"Unknown EVM version: '{version}'") from None

    def time(self) -> int:
        """Returns the current epoch time from the test RPC as an int"""
        if not self.is_active():
            raise SystemError("RPC is not active.")
        return int(time.time() + self._time_offset)

    def sleep(self, seconds: int) -> None:
        """Increases the time within the test RPC.

        Args:
            seconds (int): Number of seconds to increase the time by."""
        if type(seconds) is not int:
            raise TypeError("seconds must be an integer value")
        self._time_offset = self._request("evm_increaseTime", [seconds])

    def mine(self, blocks: int = 1) -> str:
        """Increases the block height within the test RPC.

        Args:
            blocks (int): Number of new blocks to be mined."""
        if type(blocks) is not int:
            raise TypeError("blocks must be an integer value")
        for i in range(blocks):
            self._request("evm_mine", [])
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

    def reset(self) -> str:
        """
        Revert the EVM to the initial state when loaded.

        This action clears the undo buffer.
        """
        self._snapshot_id = None
        self._undo_buffer.clear()
        self._redo_buffer.clear()
        self._reset_id = self._current_id = self._revert(self._reset_id)
        return f"Block height reset to {web3.eth.blockNumber}"


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


def _check_connections(proc: psutil.Process, laddr: Tuple) -> bool:
    try:
        return laddr in [i.laddr for i in proc.connections()]
    except psutil.AccessDenied:
        return False


def _validate_cmd_settings(cmd_settings: dict) -> dict:
    CMD_TYPES = {
        "port": int,
        "gas_limit": int,
        "block_time": int,
        "time": datetime.datetime,
        "accounts": int,
        "evm_version": str,
        "mnemonic": str,
        "account_keys_path": str,
        "fork": str,
    }
    for cmd, value in cmd_settings.items():
        if (
            cmd in CLI_FLAGS.keys()
            and cmd in CMD_TYPES.keys()
            and not isinstance(value, CMD_TYPES[cmd])
        ):
            raise TypeError(
                f'Wrong type for cmd_settings "{cmd}": {value}. '
                f"Found {type(value).__name__}, but expected {CMD_TYPES[cmd].__name__}."
            )

    if "default_balance" in cmd_settings:
        try:
            cmd_settings["default_balance"] = int(cmd_settings["default_balance"])
        except ValueError:
            # convert any input to ether, then format it properly
            default_eth = Wei(cmd_settings["default_balance"]).to("ether")
            cmd_settings["default_balance"] = (
                default_eth.quantize(1) if default_eth > 1 else default_eth.normalize()
            )
    return cmd_settings
