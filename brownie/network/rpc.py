#!/usr/bin/python3

import atexit
import psutil
from subprocess import DEVNULL, PIPE
import sys
import time

from .web3 import Web3

from brownie.types.types import _Singleton
from brownie.exceptions import RPCProcessError, RPCConnectionError, RPCRequestError


web3 = Web3()


class Rpc(metaclass=_Singleton):

    '''Methods for interacting with ganache-cli when running a local
    RPC environment.

    Account balances, contract containers and transaction history are
    automatically modified when the RPC is terminated, reset or reverted.'''

    def __init__(self):
        self._rpc = None
        self._time_offset = 0
        self._snapshot_id = False
        self._internal_id = False
        self._reset_id = False
        self._objects = []
        atexit.register(self._at_exit)

    def _at_exit(self):
        if not self.is_active():
            return
        if self._rpc.parent() == psutil.Process():
            self.kill(False)
        else:
            self._request("evm_revert", [self._reset_id])

    def launch(self, cmd):
        '''Launches the RPC client.

        Args:
            cmd: command string to execute as subprocess'''
        if self.is_active():
            raise SystemError("RPC is already active.")
        try:
            self._rpc = psutil.Popen(
                cmd.split(" "),
                stdin=DEVNULL,
                stdout=PIPE,
                stderr=PIPE,
                bufsize=1
            )
        except FileNotFoundError:
            if sys.platform == "win32" and cmd.split(" ")[0][-4:] != ".cmd":
                if " " in cmd:
                    cmd = cmd.replace(" ", ".cmd ", 1)
                else:
                    cmd += ".cmd"
                return self.launch(cmd)
            raise
        self._time_offset = 0
        self._snapshot_id = False
        self._reset_id = False
        uri = web3.providers[0].endpoint_uri if web3.providers else None
        # check if process loads successfully
        self._rpc.stdout.peek()
        time.sleep(0.1)
        if self._rpc.poll():
            raise RPCProcessError(cmd, self._rpc, uri)
        # check that web3 can connect
        if not web3.providers:
            self._reset()
            return
        for i in range(50):
            time.sleep(0.05)
            if web3.isConnected():
                self._reset_id = self._snap()
                self._reset()
                return
        rpc = self._rpc
        self.kill(False)
        raise RPCConnectionError(cmd, rpc, uri)

    def attach(self, laddr):
        '''Attaches to an already running RPC client subprocess.

        Args:
            laddr: Address that the client is listening at. Can be supplied as a
                   string "http://127.0.0.1:8545" or tuple ("127.0.0.1", 8545)'''
        if self.is_active():
            raise SystemError("RPC is already active.")
        if type(laddr) is str:
            ip, port = laddr.strip('https://').split(':')
            laddr = (ip, int(port))
        try:
            proc = next(i for i in psutil.net_connections() if i.laddr == laddr)
        except StopIteration:
            raise ProcessLookupError("Could not find RPC process.")
        self._rpc = psutil.Process(proc.pid)
        if web3.providers:
            self._reset_id = self._snap()
        self._reset()

    def kill(self, exc=True):
        '''Terminates the RPC process and all children with SIGKILL.

        Args:
            exc: if True, raises SystemError if subprocess is not active.'''
        if not self.is_active():
            if not exc:
                return
            raise SystemError("RPC is not active.")
        for child in self._rpc.children():
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        self._rpc.kill()
        self._time_offset = 0
        self._snapshot_id = False
        self._reset_id = False
        self._rpc = None
        self._reset()

    def _request(self, *args):
        if not self.is_active():
            raise SystemError("RPC is not active.")
        try:
            response = web3.providers[0].make_request(*args)
            if 'result' in response:
                return response['result']
        except IndexError:
            raise RPCConnectionError("Web3 is not connected.")
        raise RPCRequestError(response['error']['message'])

    def _snap(self):
        return self._request("evm_snapshot", [])

    def _revert(self, id_):
        if web3.isConnected() and web3.eth.blockNumber == 0:
            return self._snap()
        self._request("evm_revert", [id_])
        id_ = self._snap()
        self.sleep(0)
        for i in self._objects:
            if web3.eth.blockNumber == 0:
                i._reset()
            else:
                i._revert()
        return id_

    def _reset(self):
        for i in self._objects:
            i._reset()

    def is_active(self):
        '''Returns True if Rpc client is currently active.'''
        if not self._rpc:
            return False
        if type(self._rpc) is psutil.Popen:
            self._rpc.poll()
        return self._rpc.is_running()

    def is_child(self):
        '''Returns True if the Rpc client is active and was launched by Brownie.'''
        if not self.is_active():
            return False
        return self._rpc.parent() == psutil.Process()

    def time(self):
        '''Returns the current epoch time from the test RPC as an int'''
        if not self.is_active():
            raise SystemError("RPC is not active.")
        return int(time.time()+self._time_offset)

    def sleep(self, seconds):
        '''Increases the time within the test RPC.

        Args:
            seconds (int): Number of seconds to increase the time by.'''
        if type(seconds) is not int:
            raise TypeError("seconds must be an integer value")
        self._time_offset = self._request("evm_increaseTime", [seconds])

    def mine(self, blocks=1):
        '''Increases the block height within the test RPC.

        Args:
            blocks (int): Number of new blocks to be mined.'''
        if type(blocks) is not int:
            raise TypeError("blocks must be an integer value")
        for i in range(blocks):
            self._request("evm_mine", [])
        return "Block height at {}".format(web3.eth.blockNumber)

    def snapshot(self):
        '''Takes a snapshot of the current state of the EVM.'''
        self._snapshot_id = self._snap()
        return "Snapshot taken at block height {}".format(web3.eth.blockNumber)

    def revert(self):
        '''Reverts the EVM to the most recently taken snapshot.'''
        if not self._snapshot_id:
            raise ValueError("No snapshot set")
        self._internal_id = None
        self._snapshot_id = self._revert(self._snapshot_id)
        return "Block height reverted to {}".format(web3.eth.blockNumber)

    def reset(self):
        '''Reverts the EVM to the genesis state.'''
        self._snapshot_id = None
        self._internal_id = None
        self._reset_id = self._revert(self._reset_id)
        return "Block height reset to 0"

    def _internal_snap(self):
        if not self._internal_id:
            self._internal_id = self._snap()

    def _internal_clear(self):
        self._internal_id = None

    def _internal_revert(self):
        self._request("evm_revert", [self._internal_id])
        self._internal_id = None
        self.sleep(0)
        for i in self._objects:
            i._revert()
