#!/usr/bin/python3

from subprocess import Popen, DEVNULL
import sys
import time
from web3 import Web3, HTTPProvider

from lib.services import config
CONFIG = config.CONFIG


class web3:

    def __init__(self):
        self._init = True

    def _connect(self):
        web3 = Web3(HTTPProvider(CONFIG['active_network']['host']))
        for name, fn in [(i,getattr(web3,i)) for i in dir(web3) if i[0].islower()]:
            setattr(self, name, fn)
        for i in range(20):
            if web3.isConnected():
                return
            time.sleep(0.2)
        raise ConnectionError("Could not connect to {}".format(
            CONFIG['active_network']['host']
        ))

class Rpc:

    def __init__(self, network):
        self._rpc = Popen(
            CONFIG['active_network']['test-rpc'].split(' '),
            stdout = DEVNULL,
            stdin = DEVNULL,
            stderr = DEVNULL,
            start_new_session = True
        )
        self._time_offset = 0
        self._snapshot_id = False
        self._network = network

    def __del__(self):
        self._rpc.terminate()

    def _kill(self):
        self._rpc.terminate()

    def time(self):
        return int(time.time()+self._time_offset)

    def sleep(self, seconds):
        if type(seconds) is not int:
            raise TypeError("seconds must be an integer value")
        self._time_offset = web3.providers[0].make_request(
            "evm_increaseTime", [seconds]
        )['result']

    def mine(self, blocks = 1):
        if type(blocks) is not int:
            raise TypeError("blocks must be an integer value")
        for i in range(blocks):
             web3.providers[0].make_request("evm_mine",[])
        return "Block height at {}".format(web3.eth.blockNumber)

    def snapshot(self):
        self._snapshot_id = web3.providers[0].make_request("evm_snapshot",[])['result']
        return "Snapshot taken at block height {}".format(web3.eth.blockNumber)

    def revert(self):
        if not self._snapshot_id:
            raise ValueError("No snapshot set")
        web3.providers[0].make_request("evm_revert",[self._snapshot_id])
        self.snapshot()
        self._network._network_dict['accounts']._check_nonce()
        height = web3.eth.blockNumber
        history = self._network._network_dict['history']
        while history and (
            history[-1].block_number > height or
            not history[-1].block_number
        ):
            history.pop()
        return "Block height reverted to {}".format(height)


def wei(value):
    if value is None:
        return 0
    if type(value) is float and "e+" in str(value):
        num, dec = str(value).split("e+")
        num = num.split(".") if "." in num else [num, ""]
        return int(num[0] + num[1][:int(dec)] + "0" * (int(dec) - len(num[1])))
    if type(value) is not str:
        return int(value)
    if value[:2] == "0x":
        return int(value, 16)
    for unit, dec in UNITS.items():
        if " " + unit not in value:
            continue
        num = value.split(" ")[0]
        num = num.split(".") if "." in num else [num, ""]
        return int(num[0] + num[1][:int(dec)] + "0" * (int(dec) - len(num[1])))
    try:
        return int(value)
    except ValueError:
        raise ValueError("Unknown denomination: {}".format(value))    


web3 = web3()
UNITS = {
    'kwei': 3, 'babbage': 3, 'mwei': 6, 'lovelace': 6, 'gwei': 9, 'shannon': 9,
    'microether': 12, 'szabo': 12, 'milliether': 15, 'finney': 15, 'ether': 18
}