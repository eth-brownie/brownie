#!/usr/bin/python3

import atexit
import gc
import sys
import time
import weakref
from subprocess import DEVNULL, PIPE
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import psutil

from brownie._config import EVM_EQUIVALENTS
from brownie._singleton import _Singleton
from brownie.exceptions import RPCConnectionError, RPCProcessError, RPCRequestError

from .web3 import web3

CLI_FLAGS = {
    "port": "--port",
    "gas_limit": "--gasLimit",
    "accounts": "--accounts",
    "evm_version": "--hardfork",
    "mnemonic": "--mnemonic",
    "account_keys_path": "--acctKeys",
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
        self._internal_id: Optional[int] = False
        self._reset_id: Union[int, bool] = False
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
        for key, value in [(k, v) for k, v in kwargs.items() if v]:
            cmd += f" {CLI_FLAGS[key]} {value}"
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
                self._reset_id = self._snap()
                _notify_registry(0)
                return
            time.sleep(0.1)
            if type(self._rpc) is psutil.Popen:
                self._rpc.poll()
            if not self._rpc.is_running():
                self.kill(False)
                raise RPCProcessError(cmd, self._rpc, uri)
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
            raise ProcessLookupError("Could not find RPC process.")
        print(f"Attached to local RPC client listening at '{laddr[0]}:{laddr[1]}'...")
        self._rpc = psutil.Process(proc.pid)
        if web3.provider:
            self._reset_id = self._snap()
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

    def _internal_snap(self) -> None:
        self._internal_id = self._snap()

    def _internal_revert(self) -> None:
        self._request("evm_revert", [self._internal_id])
        self._internal_id = None
        self.sleep(0)
        _notify_registry()

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
        """Takes a snapshot of the current state of the EVM."""
        self._snapshot_id = self._snap()
        return f"Snapshot taken at block height {web3.eth.blockNumber}"

    def revert(self) -> str:
        """Reverts the EVM to the most recently taken snapshot."""
        if not self._snapshot_id:
            raise ValueError("No snapshot set")
        self._internal_id = None
        self._snapshot_id = self._revert(self._snapshot_id)
        return f"Block height reverted to {web3.eth.blockNumber}"

    def reset(self) -> str:
        """Reverts the EVM to the genesis state."""
        self._snapshot_id = None
        self._internal_id = None
        self._reset_id = self._revert(self._reset_id)
        return "Block height reset to 0"


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
