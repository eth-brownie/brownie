#!/usr/bin/python3

import atexit
import datetime
import sys
import time
import warnings
from subprocess import DEVNULL, PIPE
from typing import Any, Callable, Dict, Optional, Tuple, Union
from urllib.parse import urlparse

import psutil
from hexbytes import HexBytes

from brownie._config import EVM_EQUIVALENTS
from brownie._singleton import _Singleton
from brownie.convert import Wei
from brownie.exceptions import (
    InvalidArgumentWarning,
    RPCConnectionError,
    RPCProcessError,
    RPCRequestError,
)

from .state import Chain
from .web3 import web3

chain = Chain()

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
    "unlock": "--unlock",
}

EVM_VERSIONS = ["byzantium", "constantinople", "petersburg", "istanbul"]
EVM_DEFAULT = "istanbul"


def rpc_deprecation(fn: Callable) -> Callable:
    def wrapped(*args: Any, **kwargs: Any) -> Callable:
        warnings.warn(
            f"rpc.{fn.__name__} has been deprecated, use chain.{fn.__name__} instead",
            FutureWarning,
            stacklevel=2,
        )
        return fn(*args, **kwargs)

    return wrapped


class Rpc(metaclass=_Singleton):

    """Methods for interacting with ganache-cli when running a local
    RPC environment.

    Account balances, contract containers and transaction history are
    automatically modified when the RPC is terminated, reset or reverted."""

    def __init__(self) -> None:
        self._rpc: Any = None
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
        cmd_list = cmd.split(" ")
        kwargs.setdefault("evm_version", EVM_DEFAULT)  # type: ignore
        if kwargs["evm_version"] in EVM_EQUIVALENTS:
            kwargs["evm_version"] = EVM_EQUIVALENTS[kwargs["evm_version"]]  # type: ignore
        kwargs = _validate_cmd_settings(kwargs)
        for key, value in [(k, v) for k, v in kwargs.items() if v]:
            if key == "unlock":
                if not isinstance(value, list):
                    value = [value]  # type: ignore
                for address in value:
                    if isinstance(address, int):
                        address = HexBytes(address.to_bytes(20, "big")).hex()
                    cmd_list.extend([CLI_FLAGS[key], address])
            else:
                try:
                    cmd_list.extend([CLI_FLAGS[key], str(value)])
                except KeyError:
                    warnings.warn(
                        f"Ignoring invalid commandline setting for ganache-cli: "
                        f'"{key}" with value "{value}".',
                        InvalidArgumentWarning,
                    )
        print(f"\nLaunching '{' '.join(cmd_list)}'...")
        out = DEVNULL if sys.platform == "win32" else PIPE
        self._rpc = psutil.Popen(cmd_list, stdin=DEVNULL, stdout=out, stderr=out)
        # check that web3 can connect
        if not web3.provider:
            chain._network_disconnected()
            return
        uri = web3.provider.endpoint_uri if web3.provider else None
        for i in range(100):
            if web3.isConnected():
                chain._network_connected()
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
        chain._network_connected()

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
        self._rpc = None
        chain._network_disconnected()

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

    @rpc_deprecation
    def undo(self, num: int = 1) -> int:
        return chain.undo(num)

    @rpc_deprecation
    def redo(self, num: int = 1) -> int:
        return chain.redo(num)

    @rpc_deprecation
    def time(self) -> int:
        return chain.time()

    @rpc_deprecation
    def sleep(self, seconds: int) -> None:
        return chain.sleep(seconds)

    @rpc_deprecation
    def mine(self, blocks: int = 1) -> int:
        return chain.mine(blocks)

    @rpc_deprecation
    def snapshot(self) -> None:
        return chain.snapshot()

    @rpc_deprecation
    def revert(self) -> int:
        return chain.revert()

    @rpc_deprecation
    def reset(self) -> int:
        return chain.reset()


def _check_connections(proc: psutil.Process, laddr: Tuple) -> bool:
    try:
        return laddr in [i.laddr for i in proc.connections()]
    except psutil.AccessDenied:
        return False
    except psutil.ZombieProcess:
        return False
    except psutil.NoSuchProcess:
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
