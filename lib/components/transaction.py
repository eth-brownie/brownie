#!/usr/bin/python3

import eth_abi
import eth_event
from hexbytes import HexBytes
import json
import sys
import threading
import time

from lib.components import contract
from lib.components.compiler import compile_contracts
from lib.components.eth import web3
from lib.components import config
CONFIG = config.CONFIG


DEFAULT = "\x1b[0m"
DARK = "\033[90m"
COLORS = {
    -1: "\033[93m", # yellow
    0: "\033[91m", # red
    1: DEFAULT
}

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
    try:
        return next(i for i in data['data'].keys() if i[:2]=="0x")
    except StopIteration:
        raise VirtualMachineError(exc)


class TransactionReceipt:

    def __init__(self, txid, sender=None, silent=False, name=None, callback=None):
        if type(txid) is not str:
            txid = txid.hex()
        if txid == "stack":
            print(name)
            sys.exit()
        if CONFIG['logging']['tx'] and not silent:
            print("\nTransaction sent: {}".format(txid))
        tx_history.append(self)
        self.__dict__.update({
            '_trace': None,
            'fn_name': name,
            'txid': txid,
            'sender': sender,
            'receiver': None,
            'value': None,
            'gas_price': None,
            'gas_limit': None,
            'input': None,
            'nonce': None,
            'block_number': None,
            'txindex': None,
            'gas_used': None,
            'contract_address': None,
            'logs': [],
            'events': [],
            'status': -1,
            'revert_msg': None
        })
        t = threading.Thread(
            target=self._await_confirm,
            args=[silent, callback],
            daemon=True
        )
        t.start()
        try:
            t.join()
        except KeyboardInterrupt:
            if sys.argv[1] != "console":
                raise

    def _await_confirm(self, silent, callback):
        while True:
            tx = web3.eth.getTransaction(self.txid)
            if tx: break
            time.sleep(0.5)
        if not self.sender:
            self.sender = tx['from']
        self.__dict__.update({
            'receiver': tx['to'],
            'value': tx['value'],
            'gas_price': tx['gasPrice'],
            'gas_limit': tx['gas'],
            'input': tx['input'],
            'nonce': tx['nonce'],
        })
        if not tx['blockNumber'] and CONFIG['logging']['tx'] and not silent:
            print("Waiting for confirmation...")
        receipt = web3.eth.waitForTransactionReceipt(self.txid)
        self.__dict__.update({
            'block_number': receipt['blockNumber'],
            'txindex': receipt['transactionIndex'],
            'gas_used': receipt['gasUsed'],
            'contract_address': receipt['contractAddress'],
            'logs': receipt['logs'],
            'status': receipt['status']
        })
        try:
            self.events = eth_event.decode_logs(receipt['logs'], TOPICS)
        except:
            pass
        if self.fn_name and '--gas' in sys.argv:
            _profile_gas(self.fn_name, receipt['gasUsed'])
        if not self.status:
            try:
                trace = self.debug()
                memory = trace[-1]['memory']
                try:
                    idx = memory.index(next(i for i in memory if i[:8] == "08c379a0"))
                    data = HexBytes("".join(memory[idx:])[8:]+"00000000")
                    self.revert_msg = eth_abi.decode_abi(["string"], data)[0].decode()
                except StopIteration:
                    pass
                try:
                    self.events = eth_event.decode_trace(trace, TOPICS)
                except:
                    pass
            except ValueError:
                pass
        if not silent:
            if CONFIG['logging']['tx'] >= 2:
                self.info()
            elif CONFIG['logging']['tx']:
                print("{} confirmed {}- block: {}   gas used: {} ({:.2%})".format(
                    self.fn_name or "Transaction",
                    "" if self.status else "({}{}{}) ".format(
                        COLORS[0],
                        self.revert_msg or "reverted",
                        DEFAULT
                    ),
                    self.block_number,
                    self.gas_used,
                    self.gas_used / self.gas_limit
                ))
                if receipt['contractAddress']:
                    print("{} deployed at: {}".format(
                        self.fn_name.split('.')[0],
                        receipt['contractAddress']
                    ))
        if callback:
            callback(self)

    def __repr__(self):
        return "<Transaction object '{}{}{}'>".format(
            COLORS[self.status], self.txid, DEFAULT
        )

    def info(self):
        return _print_tx(self)

    def debug(self):
        if not self._trace:
            trace = web3.providers[0].make_request(
                'debug_traceTransaction',
                [self.txid,{}]
            )['result']['structLogs']
            if 'error' in trace:
                raise ValueError(trace['error']['message'])
            self._trace = trace
        return self._trace
    
    def call_path(self):
        path = [(self.receiver or self.contract_address, 1)]
        
        trace = self.debug()
        idx = [i for i in range(len(trace)-1) if trace[i]['op'] in (
            "CALL", "CALLCODE", "DELEGATECALL", "STATICCALL", "RETURN"
        ) and trace[i+1]['depth']!=trace[i]['depth']]
        for log in [trace[i] for i in idx]:
            if log['op'] != "RETURN":
                path.append((
                    web3.toChecksumAddress(log['stack'][-2][-40:]),
                    path[-1][1] + 1
                ))
            else:
                path.append(
                    next(i for i in path[::-1] if i[1]+1 == path[-1][1])
                )
        for i in path[:-1]:
            _print_path(i[0], i[1], COLORS[-1])
        _print_path(path[-1][0], path[-1][1], COLORS[
            0 if self.debug()[-1]['op'] != "RETURN" else -1
        ])


TX_INFO = """
Transaction was Mined{3}
---------------------
Tx Hash: {0.txid}
From: {1}
{2}
Block: {0.block_number}
Gas Used: {0.gas_used} / {0.gas_limit} ({4:.1%})
"""


def _print_tx(tx):
    print(TX_INFO.format(
        tx,
        tx.sender if type(tx.sender) is str else tx.sender.address,
        (
            "New Contract Address: "+tx.contract_address if tx.contract_address
            else "To: {0.receiver}\nValue: {0.value}{1}".format(
                tx, "\nFunction: {}".format(tx.fn_name) if tx.input!="0x00" else ""
            )
        ),
        "" if tx.status else " ({}{}{})".format(
            COLORS[0],
            tx.revert_msg or "reverted",
            DEFAULT,
        ),
        tx.gas_used / tx.gas_limit
    ))
    if tx.events:
        print("    Events In This Transaction\n    ---------------------------")
        for event in tx.events:
            print("    "+event['name'])
            for i in event['data']:
                print("        {0[name]}: {1}{0[value]}{2}".format(
                    i, DARK if not i['decoded'] else "", DEFAULT)
                )
        print()


def _print_path(address, depth, color):
    c = contract.find_contract(address)
    if c:
        result = "{}{}  {}{}".format(color,c._name,DARK,address)
    else:
        result = color+address
    print("    "*depth+result+DEFAULT)


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
        topics,
        open(CONFIG['folders']['brownie']+"/topics.json", 'w'),
        sort_keys=True,
        indent=4
    )
    return topics

TOPICS = _generate_topics()