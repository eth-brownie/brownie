#!/usr/bin/python3

import atexit
from subprocess import Popen, DEVNULL
import sys
from threading import Thread
import time

from .web3 import Web3
from .account import Accounts
from .history import TxHistory, _ContractHistory
from brownie.types.types import _Singleton
import brownie._config as config
CONFIG = config.CONFIG

web3 = Web3()

class Rpc(metaclass=_Singleton):

    '''Methods for interacting with ganache-cli when running a local
    RPC environment.'''

    def __init__(self):
        self._rpc = None
        self._time_offset = 0
        self._snapshot_id = False
        self._reset_id = False
        atexit.register(self.kill, False)

    def launch(self, cmd):
        if self.is_active():
            raise SystemError("RPC is already active.")
        self._rpc = Popen(
            cmd.split(" "),
            stdout=DEVNULL,
            stdin=DEVNULL,
            stderr=DEVNULL
        )
        self._time_offset = 0
        self._snapshot_id = False
        self._reset_id = False
        if not web3.providers:
            _reset()
            return
        for i in range(50):
            if web3.isConnected():
                self._reset_id = self._snap()
                _reset()
                return
            time.sleep(0.05)
        raise ConnectionError(
            "Cannot connect to RPC client at {}".format(web3.providers[0].endpoint_uri)
        )

    def kill(self, exc=True):
        if not self.is_active():
            if not exc:
                return
            raise SystemError("RPC is not active.")
        self._rpc.terminate()
        self._time_offset = 0
        self._snapshot_id = False
        self._reset_id = False
        self._rpc = None
        _reset()

    def _request(self, *args):
        if not self.is_active():
            raise SystemError("RPC is not active.")
        try:
            return web3.providers[0].make_request(*args)['result']
        except IndexError:
            raise ConnectError("Web3 is not connected.")

    def _snap(self):
        return self._request("evm_snapshot", [])

    def _revert(self, id_):
        if web3.eth.blockNumber == 0:
            return self._snap()
        self._request("evm_revert", [id_])
        id_ = self._snap()
        self.sleep(0)
        _revert()
        return id_

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
        self._snapshot_id = self._revert(self._snapshot_id)
        return "Block height reverted to {}".format(web3.eth.blockNumber)

    def reset(self):
        self._request("evm_revert", [self._reset_id])
        self._snaptshot_id = None
        self._reset_id = self._revert(self._reset_id)
        return "Block height reset to 0"


def _reset():
    TxHistory()._reset()
    _ContractHistory()._reset()
    Accounts()._reset()


def _revert():
    TxHistory()._revert()
    _ContractHistory()._revert()
    Accounts()._revert()
