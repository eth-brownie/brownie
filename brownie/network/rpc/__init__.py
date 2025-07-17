#!/usr/bin/python3

import atexit
import inspect
import platform
import socket
import time
import warnings
from typing import Any, Callable, Dict, Tuple, Union
from urllib.parse import urlparse

import psutil

from brownie._singleton import _Singleton
from brownie.exceptions import RPCConnectionError, RPCProcessError
from brownie.network.state import Chain
from brownie.network.web3 import web3

from . import anvil, ganache, geth, hardhat

chain = Chain()

ATTACH_BACKENDS = {"ethereumjs testrpc": ganache, "geth": geth, "hardhat": hardhat}

LAUNCH_BACKENDS = {
    "anvil": anvil,
    "ganache": ganache,
    "ethnode": geth,
    "geth": geth,
    "npx hardhat": hardhat,
}


def internal(fn: Callable) -> Callable:
    """
    Decorator that warns when a user calls directly to Rpc methods.
    """

    def wrapped(*args: Any, **kwargs: Any) -> Callable:
        if inspect.stack()[1].frame.f_locals.get("self", None) != chain:
            warnings.warn(
                f"rpc.{fn.__name__} should not be called directly, use chain.{fn.__name__} instead",
                FutureWarning,
                stacklevel=2,
            )
        return fn(*args, **kwargs)

    return wrapped


class Rpc(metaclass=_Singleton):
    def __init__(self) -> None:
        self.process: Union[psutil.Popen, psutil.Process] = None
        self.backend: Any = ganache
        atexit.register(self._at_exit)

    def _at_exit(self) -> None:
        if not self.is_active():
            return
        if self.process.parent() == psutil.Process():
            if getattr(self.process, "stdout", None) is not None:
                self.process.stdout.close()
            if getattr(self.process, "stderr", None) is not None:
                self.process.stderr.close()
            self.kill(False)

    def launch(self, cmd: str, **kwargs: Dict) -> None:
        if self.is_active():
            raise SystemError("RPC is already active.")

        for key, module in LAUNCH_BACKENDS.items():
            if cmd.lower().startswith(key):
                self.backend = module
                break

        self.process = self.backend.launch(cmd, **kwargs)

        # check that web3 can connect
        if not web3.provider:
            chain._network_disconnected()
            return
        uri = web3.provider.endpoint_uri if web3.provider else None
        for i in range(100):
            if web3.isConnected():
                web3.reset_middlewares()
                self.backend.on_connection()
                chain._network_connected()
                return
            time.sleep(0.1)
            if isinstance(self.process, psutil.Popen):
                self.process.poll()
            if not self.process.is_running():
                self.kill(False)
                raise RPCProcessError(cmd, uri)
        self.kill(False)
        raise RPCConnectionError(cmd, self.process, uri)

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

        ip = socket.gethostbyname(laddr[0])
        resolved_addr = (ip, laddr[1])
        pid = self._find_rpc_process_pid(resolved_addr)

        print(f"Attached to local RPC client listening at '{laddr[0]}:{laddr[1]}'...")
        self.process = psutil.Process(pid)

        for key, module in ATTACH_BACKENDS.items():
            if web3.client_version.lower().startswith(key):
                self.backend = module
                break

        web3.reset_middlewares()
        self.backend.on_connection()
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
        for child in self.process.children(recursive=True):
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        self.process.kill()
        self.process.wait()
        chain._network_disconnected()

    def is_active(self) -> bool:
        """Returns True if Rpc client is currently active."""
        if not self.process:
            return False
        if isinstance(self.process, psutil.Popen):
            self.process.poll()
        return self.process.is_running()

    def is_child(self) -> bool:
        """Returns True if the Rpc client is active and was launched by Brownie."""
        if not self.is_active():
            return False
        return self.process.parent() == psutil.Process()

    @internal
    def sleep(self, seconds: int) -> int:
        return self.backend.sleep(seconds)

    @internal
    def mine(self, timestamp: int = None) -> int:
        self.backend.mine(timestamp)
        return web3.eth.block_number

    @internal
    def snapshot(self) -> int:
        return self.backend.snapshot()

    @internal
    def revert(self, snapshot_id: int) -> int:
        self.backend.revert(snapshot_id)
        return web3.eth.block_number

    def unlock_account(self, address: str) -> None:
        self.backend.unlock_account(address)

    def _find_rpc_process_pid(self, laddr: Tuple) -> int:
        try:
            # default case with an already running local RPC process
            return self._get_pid_from_connections(laddr)
        except ProcessLookupError:
            # if no local RPC process could be found we can try to find a dockerized one
            if platform.system() == "Darwin":
                return self._get_pid_from_docker_backend()
            else:
                return self._get_pid_from_net_connections(laddr)

    def _check_proc_connections(self, proc: psutil.Process, laddr: Tuple) -> bool:
        try:
            return laddr in [i.laddr for i in proc.connections()]
        except psutil.AccessDenied:
            return False
        except psutil.ZombieProcess:
            return False
        except psutil.NoSuchProcess:
            return False

    def _check_net_connections(self, connection: Any, laddr: Tuple) -> bool:
        if connection.pid is None:
            return False
        if connection.laddr == laddr:
            return True
        elif connection.raddr == laddr:
            return True
        else:
            return False

    def _get_pid_from_connections(self, laddr: Tuple) -> int:
        try:
            proc = next(i for i in psutil.process_iter() if self._check_proc_connections(i, laddr))
            return self._get_proc_pid(proc)
        except StopIteration:
            raise ProcessLookupError(
                "Could not attach to RPC process by querying 'proc.connections()'"
            ) from None

    def _get_pid_from_net_connections(self, laddr: Tuple) -> int:
        try:
            proc = next(
                i
                for i in psutil.net_connections(kind="tcp")
                if self._check_net_connections(i, laddr)
            )
            return self._get_proc_pid(proc)
        except StopIteration:
            raise ProcessLookupError(
                "Could not attach to RPC process by querying 'proc.net_connections()'"
            ) from None

    def _get_pid_from_docker_backend(self) -> int:
        # OSX workaround for https://github.com/giampaolo/psutil/issues/1219
        proc = self._find_proc_by_name("com.docker.backend")
        return self._get_proc_pid(proc)

    def _get_proc_pid(self, proc: psutil.Process) -> int:
        if proc:
            return proc.pid
        else:
            raise ProcessLookupError(
                "Could not attach to RPC process. If this issue persists, try killing "
                "the RPC and let Brownie launch it as a child process."
            ) from None

    def _find_proc_by_name(self, process_name: str) -> psutil.Process:
        for proc in psutil.process_iter():
            if process_name.lower() in proc.name().lower():
                return proc
