#!/usr/bin/python3

from subprocess import Popen, DEVNULL
from threading import Thread
import time
from web3 import Web3, HTTPProvider

import brownie._registry as _registry
import brownie.config as config
CONFIG = config.CONFIG




class Rpc:

    '''Methods for interacting with ganache-cli when running a local
    RPC environment.'''

    def __init__(self):
        rpc = Popen(
            CONFIG['active_network']['test-rpc'].split(' '),
            stdout=DEVNULL,
            stdin=DEVNULL,
            stderr=DEVNULL,
            start_new_session=True
        )
        self._rpc = rpc
        self._time_offset = 0
        self._snapshot_id = False
        #self._network = network
        Thread(target=_watch_rpc, args=[rpc], daemon=True).start()
        _registry.add(self)
        _registry.active['rpc'] = self
        connect()

    def __del__(self):
        self._rpc.terminate()
        if _registry:
            _registry.remove(self)
            _registry.active['rpc'] = None

    def kill(self):
        _registry.remove(self)
        _registry.active['rpc'] = None
        self._rpc.terminate()

    def _request(self, *args):
        return self.web3.providers[0].make_request(*args)
        
    
    def time(self):
        '''Returns the current epoch time from the test RPC as an int'''
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
    print("{0[error]}ERROR{0}: Local RPC has terminated with exit code {0[value]}{1}{0}".format(
        color, rpc.poll()
    ))


def launch_rpc():
    if _registry.active['rpc']:
        raise ConnectionError("RPC already active")
    return Rpc()


def connect():
    web3 = Web3(HTTPProvider(CONFIG['active_network']['host']))
    for i in range(20):
        if web3.isConnected():
            _registry.set_web3(web3)
            return web3
        time.sleep(0.2)
    raise ConnectionError("Could not connect to {}".format(
        CONFIG['active_network']['host']
    ))


def get_rpc():
    return _registry.active['rpc']