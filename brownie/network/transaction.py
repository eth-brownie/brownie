#!/usr/bin/python3

import threading
import time

import eth_abi
from hexbytes import HexBytes

from brownie.cli.utils import color
from brownie.exceptions import VirtualMachineError
from brownie.network.history import history
from brownie.network.event import decode_logs, decode_trace
from brownie.network.web3 import web3
from brownie.types import KwargTuple
from brownie.types.convert import format_output

import brownie._config as config
CONFIG = config.CONFIG


TX_INFO = """
Transaction was Mined{4}
---------------------
{0[key]}Tx Hash{0}: {0[value]}{1.txid}{0}
{0[key]}From{0}: {0[value]}{2}{0}
{0[key]}{3}{0}
{0[key]}Block{0}: {0[value]}{1.block_number}{0}
{0[key]}Gas Used{0}: {0[value]}{1.gas_used}{0} / {0[value]}{1.gas_limit}{0} ({0[value]}{5:.1%}{0})
"""


gas_profile = {}


class TransactionReceipt:

    '''Attributes and methods relating to a broadcasted transaction.

    * All ether values are given in wei.
    * Before the tx confirms, many values are set to None.
    * trace, revert_msg return_value, and events from a reverted tx
      are only available if debug_traceTransaction is enabled in the RPC.

    Attributes:
        fn_name: Name of the method called in the transaction
        txid: Transaction ID
        sender: Address of the sender
        receiver: Address of the receiver
        value: Amount transferred
        gas_price: Gas price
        gas_limit: Gas limit
        gas_used: Gas used
        input: Hexstring input data
        nonce: Transaction nonce
        txindex: Index of the transaction within the mined block
        contract_address: Address of contract deployed by the transaction
        logs: Raw transaction logs
        status: Transaction status: -1 pending, 0 reverted, 1 successful
        events: Decoded transaction log events
        trace: Stack trace from debug_traceTransaction
        return_value: Returned value from contract call
        revert_msg: Error string from reverted contract all'''

    def __init__(self, txid, sender=None, silent=False, name='', callback=None):
        if type(txid) is not str:
            txid = txid.hex()
        if CONFIG['logging']['tx'] and not silent:
            print("\n{0[key]}Transaction sent{0}: {0[value]}{1}{0}".format(color, txid))
        history._add_tx(self)
        self.__dict__.update({
            '_trace': None,
            'fn_name': name,
            'txid': txid,
            'sender': sender,
            'receiver': None,
            'value': None,
            'gas_price': None,
            'gas_limit': None,
            'gas_used': None,
            'input': None,
            'nonce': None,
            'block_number': None,
            'txindex': None,
            'contract_address': None,
            'logs': [],
            'status': -1,
        })
        t = threading.Thread(
            target=self._await_confirm,
            args=[silent, callback],
            daemon=True
        )
        t.start()
        try:
            t.join()
            if config.ARGV['cli'] == "console":
                return
            if config.ARGV['coverage']:
                self.trace
            if not self.status:
                raise VirtualMachineError({
                    "message": "revert "+(self.revert_msg or ""),
                    "source": self.error(1)
                })
        except KeyboardInterrupt:
            if config.ARGV['cli'] != "console":
                raise

    def _await_confirm(self, silent, callback):
        while True:
            tx = web3.eth.getTransaction(self.txid)
            if tx:
                break
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
        if tx['to'] and history.find_contract(tx['to']) is not None:
            self.receiver = history.find_contract(tx['to'])
            if not self.fn_name:
                self.fn_name = "{}.{}".format(
                    self.receiver._name,
                    self.receiver.get_method(tx['input'])
                )
        if not tx['blockNumber'] and CONFIG['logging']['tx'] and not silent:
            print("Waiting for confirmation...")
        receipt = web3.eth.waitForTransactionReceipt(self.txid, None)
        self.__dict__.update({
            'block_number': receipt['blockNumber'],
            'txindex': receipt['transactionIndex'],
            'gas_used': receipt['gasUsed'],
            'contract_address': receipt['contractAddress'],
            'logs': receipt['logs'],
            'status': receipt['status']
        })
        self.events = decode_logs(receipt['logs'])
        if self.fn_name and config.ARGV['gas']:
            _profile_gas(self.fn_name, receipt['gasUsed'])
        if not silent:
            if CONFIG['logging']['tx'] >= 2:
                self.info()
            elif CONFIG['logging']['tx']:
                print(
                    ("{1} confirmed {2}- {0[key]}block{0}: {0[value]}{3}{0}   "
                    "{0[key]}gas used{0}: {0[value]}{4}{0} ({0[value]}{5:.2%}{0})").format(
                    color,
                    self.fn_name or "Transaction",
                    "" if self.status else "({0[error]}{1}{0}) ".format(
                        color,
                        self.revert_msg or "reverted"
                    ),
                    self.block_number,
                    self.gas_used,
                    self.gas_used / self.gas_limit
                ))
                if receipt['contractAddress']:
                    print("{1} deployed at: {0[value]}{2}{0}".format(
                        color,
                        self.fn_name.split('.')[0],
                        receipt['contractAddress']
                    ))
        if callback:
            callback(self)

    def __repr__(self):
        c = {-1: 'pending', 0: 'error', 1: None}
        return "<Transaction object '{}{}{}'>".format(
            color(c[self.status]), self.txid, color
        )

    def __hash__(self):
        return hash(self.txid)

    def __getattr__(self, attr):
        if attr not in ('events', 'return_value', 'revert_msg', 'trace', '_trace'):
            raise AttributeError(
                "'TransactionReceipt' object has no attribute '{}'".format(attr)
            )
        if self.status == -1:
            return None
        if self._trace is None:
            self._get_trace()
        if attr == "trace":
            self._evaluate_trace()
        return self.__dict__[attr]

    def info(self):
        '''Displays verbose information about the transaction, including
        decoded event logs.'''
        if self.contract_address:
            line = "New Contract Address{0}: {0[value]}{1}".format(color, self.contract_address)
        else:
            line = "To{0}: {0[value]}{1.receiver}{0}\n{0[key]}Value{0}: {0[value]}{1.value}".format(color, self)
            if self.input != "0x00":
                line += "\n{0[key]}Function{0}: {0[value]}{1}".format(color, self.fn_name)
        print(TX_INFO.format(
            color,
            self,
            self.sender if type(self.sender) is str else self.sender.address,
            line,
            "" if self.status else " ({0[error]}{1}{0})".format(
                color, self.revert_msg or "reverted"
            ),
            self.gas_used / self.gas_limit
        ))
        if self.events:
            print("   Events In This Transaction\n   --------------------------")
            for event in self.events:
                print("   "+color('bright yellow')+event['name']+color())
                for i in event['data']:
                    print("      {0[key]}{1[name]}{0}: {2}{1[value]}{0}".format(
                        color, i, color['value' if i['decoded'] else 'dull']
                    ))
            print()

    def _get_trace(self):
        '''Retrieves the stack trace via debug_traceTransaction, and finds the
        return value, revert message and event logs in the trace.'''
        self.return_value = None
        self.revert_msg = None
        self._trace = []
        if (self.input == "0x" and self.gas_used == 21000) or self.contract_address:
            self.trace = []
            return
        trace = web3.providers[0].make_request(
            'debug_traceTransaction',
            [self.txid, {}]
        )
        if 'error' in trace:
            raise ValueError(trace['error']['message'])
        self._trace = trace = trace['result']['structLogs']
        if self.status:
            # get return value
            log = trace[-1]
            if log['op'] != "RETURN":
                return
            c = self.contract_address or self.receiver
            if type(c) is str:
                return
            abi = [
                i['type'] for i in
                getattr(c, self.fn_name.split('.')[-1]).abi['outputs']
            ]
            offset = int(log['stack'][-1], 16) * 2
            length = int(log['stack'][-2], 16) * 2
            data = HexBytes("".join(log['memory'])[offset:offset+length])
            self.return_value = eth_abi.decode_abi(abi, data)
            if not self.return_value:
                return
            if len(self.return_value) == 1:
                self.return_value = format_output(self.return_value[0])
            else:
                self.return_value = KwargTuple(
                    self.return_value,
                    getattr(c, self.fn_name.split('.')[-1]).abi
                )
        else:
            # get revert message
            self.revert_msg = ""
            if trace[-1]['op'] == "REVERT":
                offset = int(trace[-1]['stack'][-1], 16) * 2
                length = int(trace[-1]['stack'][-2], 16) * 2
                if length:
                    data = HexBytes("".join(trace[-1]['memory'])[offset+8:offset+length])
                    self.revert_msg = eth_abi.decode_abi(["string"], data)[0].decode()
            # get events from trace
            self.events = decode_trace(trace)

    def _evaluate_trace(self):
        '''Adds the following attributes to each step of the stack trace:

        address: The address executing this contract.
        contractName: The name of the contract.
        fn: The name of the function.
        source: Start and end offset associated source code.
        jumpDepth: Number of jumps made since entering this contract. The
                   initial value is 1.'''
        self.trace = trace = self._trace
        if not trace:
            return
        c = self.contract_address or self.receiver
        last = {0: {
            'address': c.address,
            'contract': c._name,
            'fn': [self.fn_name.split('.')[-1]],
        }}
        pc = c._build['pcMap'][0]
        trace[0].update({
            'address': last[0]['address'],
            'contractName': last[0]['contract'],
            'fn': last[0]['fn'][-1],
            'jumpDepth': 1,
            'source': {
                'filename': pc['contract'],
                'start': pc['start'],
                'stop': pc['stop']
            }
        })
        for i in range(1, len(trace)):
            # if depth has increased, tx has called into a different contract
            if trace[i]['depth'] > trace[i-1]['depth']:
                address = web3.toChecksumAddress(trace[i-1]['stack'][-2][-40:])
                c = history.find_contract(address)
                stack_idx = -4 if trace[i-1]['op'] in ('CALL', 'CALLCODE') else -3
                memory_idx = int(trace[i-1]['stack'][stack_idx], 16) * 2
                sig = "0x" + "".join(trace[i-1]['memory'])[memory_idx:memory_idx+8]
                last[trace[i]['depth']] = {
                    'address': address,
                    'contract': c._name,
                    'fn': [next((k for k, v in c.signatures.items() if v == sig), "")],
                    }
            trace[i].update({
                'address': last[trace[i]['depth']]['address'],
                'contractName': last[trace[i]['depth']]['contract'],
                'fn': last[trace[i]['depth']]['fn'][-1],
                'jumpDepth': len(set(last[trace[i]['depth']]['fn']))
            })
            c = history.find_contract(trace[i]['address'])
            pc = c._build['pcMap'][trace[i]['pc']]
            trace[i]['source'] = {
                'filename': pc['contract'],
                'start': pc['start'],
                'stop': pc['stop']
            }
            # jump 'i' is moving into an internal function
            if pc['jump'] == 'i':
                source = c._build['source'][pc['start']:pc['stop']]
                if source[:7] not in ("library", "contrac") and "(" in source:
                    fn = source[:source.index('(')].split('.')[-1]
                else:
                    fn = last[trace[i]['depth']]['fn'][-1]
                last[trace[i]['depth']]['fn'].append(fn)
            # jump 'o' is coming out of an internal function
            elif pc['jump'] == "o" and len(last[trace[i]['depth']]['fn']) > 1:
                last[trace[i]['depth']]['fn'].pop()

    def call_trace(self):
        '''Displays the sequence of contracts and functions called while
        executing this transaction, and the structLog index where each call
        or jump occured. Any functions that terminated with REVERT or INVALID
        opcodes are highlighted in red.'''
        trace = self.trace
        sep = max(i['jumpDepth'] for i in trace)
        idx = 0
        for i in range(1, len(trace)):
            if (
                trace[i]['depth'] == trace[i-1]['depth'] and
                trace[i]['jumpDepth'] == trace[i-1]['jumpDepth']
            ):
                continue
            _print_path(trace[i-1], idx, sep)
            idx = i
        _print_path(trace[-1], idx, sep)

    def error(self, pad=3):
        '''Displays the source code that caused the transaction to revert.'''
        try:
            idx = self.trace.index(next(i for i in self.trace if i['op'] in ("REVERT", "INVALID")))
        except StopIteration:
            return ""
        while True:
            if idx == -1:
                return ""
            if not self.trace[idx]['source']['filename']:
                idx -= 1
                continue
            span = (self.trace[idx]['source']['start'], self.trace[idx]['source']['stop'])
            c = history.find_contract(self.trace[idx]['address'])
            if c._build['sourcePath'] != self.trace[idx]['source']['filename']:
                source = open(self.trace[idx]['source']['filename']).read()
            else:
                source = c._build['source']
            if source[span[0]][:8] in ("contract", "library "):
                idx -= 1
                continue
            newlines = [i for i in range(len(source)) if source[i] == "\n"]
            try:
                start = newlines.index(next(i for i in newlines if i >= span[0]))
                stop = newlines.index(next(i for i in newlines if i >= span[1]))
                break
            except StopIteration:
                idx -= 1
        ln = start + 1
        start = newlines[max(start-(pad+1), 0)]
        stop = newlines[min(stop+pad, len(newlines)-1)]
        result = ((
            '{0[dull]}File {0[string]}"{1}"{0[dull]}, ' +
            'line {0[value]}{2}{0[dull]}, in {0[callable]}{3}'
        ).format(color, self.trace[idx]['source']['filename'], ln, self.trace[idx]['fn']))
        result += ("{0[dull]}{1}{0}{2}{0[dull]}{3}{0}".format(
            color,
            source[start:span[0]],
            source[span[0]:span[1]],
            source[span[1]:stop]
        ))
        return result


def _print_path(trace, idx, sep):
    col = "error" if trace['op'] in ("REVERT", "INVALID") else "pending"
    name = "{0[contractName]}.{1}{0[fn]}".format(trace, color(col))
    print(
        ("  "*sep*trace['depth']) + ("  "*(trace['jumpDepth']-1)) +
        "{}{} {}{} ({})".format(color(col), name, color('dull'), idx, trace['address']) +
        color()
    )


def _profile_gas(fn_name, gas_used):
    gas_profile.setdefault(
        fn_name,
        {
            'avg': 0,
            'high': 0,
            'low': float('inf'),
            'count': 0
        }
    )
    gas = gas_profile[fn_name]
    gas.update({
        'avg': (gas['avg']*gas['count'] + gas_used) / (gas['count']+1),
        'high': max(gas['high'], gas_used),
        'low': min(gas['low'], gas_used)
    })
    gas['count'] += 1
