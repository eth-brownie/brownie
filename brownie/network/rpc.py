#!/usr/bin/python3

import atexit
from subprocess import Popen, DEVNULL
import sys
from threading import Thread
import time

from .web3 import web3
import brownie._registry as _registry
import brownie._config as config
CONFIG = config.CONFIG


class Rpc:

    '''Methods for interacting with ganache-cli when running a local
    RPC environment.'''

    def __init__(self, web3):
        self._rpc = None
        self._time_offset = 0
        self._snapshot_id = False
        atexit.register(self.kill, False)

    def launch(self, param_str=""):
        if self.is_active():
            raise SystemError("RPC is already active.")
        if 'test-rpc' not in CONFIG['active_network']:
            raise KeyError("No test RPC defined for this network in brownie-config.json")
        try:
            self._rpc = rpc = Popen(
                (CONFIG['active_network']['test-rpc']+' '+param_str).split(' '),
                stdout=DEVNULL,
                stdin=DEVNULL,
                stderr=DEVNULL
            )
        except FileNotFoundError:
            if sys.platform == "win32" and "c:" not in CONFIG['active_network']['test-rpc'].lower():
                raise FileNotFoundError(
                    "Cannot find test RPC - check that brownie-config.json includes"
                    " the full path, with folders seperated by forward slashes."
                )
            raise FileNotFoundError("Cannot test RPC - check the filename in brownie-config.json")
        self._time_offset = 0
        self._snapshot_id = False
        for i in range(50):
            if web3.isConnected():
                _registry.reset()
                return
            time.sleep(0.1)
        raise ConnectionError(
            "Cannot connect to {}".format(web3.providers[0].endpoint_uri)
        )
        Thread(target=_watch_rpc, args=[rpc], daemon=True).start()

    def kill(self, exc=True):
        if not self.is_active():
            if not exc:
                return
            raise SystemError("RPC is not active.")
        self._rpc.terminate()
        self._time_offset = 0
        self._snapshot_id = False
        self._rpc = None
        _registry.reset()

    def _request(self, *args):
        if not self.is_active():
            raise SystemError("RPC is not active.")
        return web3.providers[0].make_request(*args)

    def is_active(self):
        return bool(self._rpc and not self._rpc.poll())

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
        self._time_offset = self._request("evm_increaseTime", [seconds])['result']

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
        self._snapshot_id = self._request("evm_snapshot", [])['result']
        return "Snapshot taken at block height {}".format(web3.eth.blockNumber)

    def revert(self):
        '''Reverts the EVM to the most recently taken snapshot.'''
        if not self._snapshot_id:
            raise ValueError("No snapshot set")
        self._request("evm_revert", [self._snapshot_id])
        self.snapshot()
        self.sleep(0)
        _registry.revert()
        return "Block height reverted to {}".format(web3.eth.blockNumber)


def _watch_rpc(rpc):
    code = rpc.wait()
    if not code or code == -15:
        return
    raise ConnectionError("Local RPC terminated with exit code {}".format(rpc.poll()))
