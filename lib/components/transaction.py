#!/usr/bin/python3

import eth_event
from hexbytes import HexBytes
import json
import sys
import time

from lib.components.compiler import compile_contracts
from lib.components.eth import web3
from lib.components import config
CONFIG = config.CONFIG


GREEN = "\033[92m"
RED = "\033[91m"
DEFAULT = "\x1b[0m"

TX_INFO="""
Transaction was Mined
---------------------
Tx Hash: {0.hash}
From: {0.from}
{1}{2}
Block: {0.blockNumber}
Gas Used: {0.gasUsed}
"""

gas_profile = {}
tx_history = []


class VirtualMachineError(Exception):

    def __init__(self, exc):
        msg = eval(str(exc))['message']
        if len(msg.split('revert ', maxsplit=1))>1:
            self.revert_msg = msg.split('revert ')[1]
        else:
            self.revert_msg = None
        super().__init__(msg)

def raise_or_return_tx(exc):
    data = eval(str(exc))
    if 'data' in data:
        return list(data['data'].keys())[0]
    raise VirtualMachineError(exc)


class TransactionReceipt:

    def __init__(self, txid, silent=False, name=None):
        if type(txid) is not str:
            txid = txid.hex()
        self.fn_name = name
        tx_history.append(self)
        while True:
            tx = web3.eth.getTransaction(txid)
            if tx: break
            time.sleep(0.5)
        if CONFIG['logging']['tx'] and not silent:
            print("\nTransaction sent: {}".format(txid))
        for k,v in tx.items():
            setattr(self, k, v.hex() if type(v) is HexBytes else v)
        if not tx.blockNumber and CONFIG['logging']['tx'] and not silent:
            print("Waiting for confirmation...")
        receipt = web3.eth.waitForTransactionReceipt(txid)
        for k,v in [(k,v) for k,v in receipt.items() if k not in tx]:
            if type(v) is HexBytes:
                v = v.hex()
            setattr(self, k, v)
        if name and '--gas' in sys.argv:
            _profile_gas(name, receipt.gasUsed)
        self.gasLimit = self.gas
        del self.gas
        self.events = []
        self.events = eth_event.decode_logs(receipt.logs, TOPICS)
        if not self.status:
            self.events = eth_event.decode_trace(web3.providers[0].make_request('debug_traceTransaction',[txid,{}]), TOPICS)
        if silent:
            return
        if CONFIG['logging']['tx'] >= 2:
            self.info()
        elif CONFIG['logging']['tx']:
            print("{} confirmed - block: {}   gas spent: {}".format(
                name or "Transaction", receipt.blockNumber, receipt.gasUsed
            ))
            if not self.contractAddress:
                return
            print("Contract deployed at: {}".format(self.contractAddress))

    def __repr__(self):
        return "<Transaction object '{}{}{}'>".format(
            DEFAULT if self.status else RED, self.hash, DEFAULT
        )
        
    def info(self):
        return _print_tx(self)


def _print_tx(tx):
    print(TX_INFO.format(
        tx,
        (
            "New Contract Address: "+tx.contractAddress if tx.contractAddress
            else "To: {0.to}\nValue: {0.value}".format(tx)
        ),
        (
            "\nFunction: {}".format(tx.fn_name) if 
            (tx.input!="0x00" and not tx.contractAddress) else ""
        )
    ))
    
    if tx.events:
        print("  Events In This Transaction\n  ---------------------------")
        for event in tx.events:
            print("  "+event['name'])
            for i in event['data']:
                print("    {0[name]}: {0[value]}".format(i))
        print()


def _profile_gas(fn_name, gas_used):
    gas_profile.setdefault(
        fn_name,
        {
            'avg':0,
            'high':0,
            'low':float('inf'),
            'count':0
        }
    )
    gas = gas_profile[fn_name]
    gas.update({
        'avg': (gas['avg']*gas['count'] + gas_used) / (gas['count']+1),
        'high': max(gas['high'], gas_used),
        'low': min(gas['low'], gas_used)
    })
    gas['count'] += 1


def _generate_topics():
    try:
        topics = json.load(open(CONFIG['folders']['brownie']+"/topics.json", 'r'))
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        topics = {}
    contracts = compile_contracts()
    events = [x for i in contracts.values() for x in i['abi'] if x['type']=="event"]
    topics.update(eth_event.get_event_abi(events))
    json.dump(
        topics, open(CONFIG['folders']['brownie']+"/topics.json", 'w'),
        sort_keys=True, indent=4
    )
    return topics

TOPICS = _generate_topics()