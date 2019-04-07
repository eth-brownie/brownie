#!/usr/bin/python3

import atexit
from subprocess import Popen, DEVNULL
from threading import Thread
import time

import brownie._registry as _registry
import brownie.config as config
CONFIG = config.CONFIG


class Rpc:

    '''Methods for interacting with ganache-cli when running a local
    RPC environment.'''

    def __init__(self, web3):
        self._rpc = None
        self._time_offset = 0
        self._snapshot_id = False
        self.web3 = None
        atexit.register(self.kill, False)

    def launch(self, *args):
        if self.is_active():
            raise SystemError("RPC is already active.")
        if 'test-rpc' not in CONFIG['active_network']:
            raise KeyError("No test RPC defined for this network in config.json")
        self._rpc = rpc = Popen(
            CONFIG['active_network']['test-rpc']+list(args).split(' '),
            stdout=DEVNULL,
            stdin=DEVNULL,
            stderr=DEVNULL,
            start_new_session=True
        )
        self._time_offset = 0
        self._snapshot_id = False
        for i in range(20):
            if self.web3.isConnected():
                _registry.reset()
                return web3
            time.sleep(0.2)
        raise ConnectionError(
            "Cannot connect to {}".format(self.web3.providers[0].endpoint_uri)
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
        _registry.reset()

    def _request(self, *args):
        if not self.is_active():
            raise SystemError("RPC is not active.")
        return self.web3.providers[0].make_request(*args)

    def is_active(self):
        return self._rpc and not self._rpc.poll()

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
        return "Block height at {}".format(self.web3.eth.blockNumber)

    def snapshot(self):
        '''Takes a snapshot of the current state of the EVM.'''
        self._snapshot_id = self._request("evm_snapshot", [])['result']
        return "Snapshot taken at block height {}".format(self.web3.eth.blockNumber)

    def revert(self):
        '''Reverts the EVM to the most recently taken snapshot.'''
        if not self._snapshot_id:
            raise ValueError("No snapshot set")
        self._request("evm_revert", [self._snapshot_id])
        self.snapshot()
        self.sleep(0)
        
        # self._network._network_dict['accounts']._check_nonce()
        # height = self.web3.eth.blockNumber
        # history = self._network._network_dict['history']
        # while history and (
        #     history[-1].block_number > height or
        #     not history[-1].block_number
        # ):
        #     history.pop()
        # return "Block height reverted to {}".format(height)


def _watch_rpc(rpc):
    code = rpc.wait()
    if not code or code == -15:
        return
    raise ConnectionError("Local RPC terminated with exit code {}".format(rpc.poll()))