#!/usr/bin/python3

from subprocess import Popen, DEVNULL
import sys
import time
from web3 import Web3, HTTPProvider

from lib.components import config
CONFIG = config.CONFIG


class web3:

    def __init__(self):
        self._rpc = None
        self._init = True

    def __del__(self):
        if self._rpc:
            self._rpc.terminate()

    def _run(self):
        if self._init or sys.argv[1] == "console":
            verbose = True
            self._init = False
        else:
            verbose = False
        if verbose:
            print("Using network '{}'".format(CONFIG['active_network']['name']))
        if self._rpc:
            if verbose:
                print("Resetting environment...")
            self._rpc.terminate()
        if 'test-rpc' in CONFIG['active_network']:
            if verbose:
                print("Running '{}'...".format(CONFIG['active_network']['test-rpc']))
            self._rpc = Popen(
                CONFIG['active_network']['test-rpc'].split(' '),
                stdout = DEVNULL,
                stdin = DEVNULL,
                stderr = DEVNULL,
                start_new_session = True
            )
        web3 = Web3(HTTPProvider(CONFIG['active_network']['host']))
        for i in range(20):
            if web3.isConnected():
                break
            if i == 19:
               raise ConnectionError("Could not connect to {}".format(CONFIG['active_network']['host']))
            time.sleep(0.2)
        for name, fn in [(i,getattr(web3,i)) for i in dir(web3) if i[0].islower()]:
            setattr(self, name, fn)


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