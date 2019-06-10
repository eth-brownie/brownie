#!/usr/bin/python3

import threading
import time

from hexbytes import HexBytes

from .web3 import Web3
from brownie.cli.utils import color
from brownie.exceptions import RPCRequestError, VirtualMachineError
from brownie.network.history import TxHistory, _ContractHistory
from brownie.network.event import decode_logs, decode_trace
from brownie.project import build, sources
from brownie.types.convert import to_string
from brownie._config import ARGV, CONFIG


TX_INFO = """
Transaction was Mined{4}
---------------------
{0[key]}Tx Hash{0}: {0[value]}{1.txid}{0}
{0[key]}From{0}: {0[value]}{2}{0}
{0[key]}{3}{0}
{0[key]}Block{0}: {0[value]}{1.block_number}{0}
{0[key]}Gas Used{0}: {0[value]}{1.gas_used}{0} / {0[value]}{1.gas_limit}{0} ({0[value]}{5:.1%}{0})
"""


history = TxHistory()
_contracts = _ContractHistory()
web3 = Web3()


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

    def __init__(self, txid, sender=None, silent=False, name='', callback=None, revert=None):
        if type(txid) is not str:
            txid = txid.hex()
        if CONFIG['logging']['tx'] and not silent:
            print("\n{0[key]}Transaction sent{0}: {0[value]}{1}{0}".format(color, txid))
        history._add_tx(self)
        self.__dict__.update({
            '_trace': None,
            '_revert_pc': None,
            'block_number': None,
            'contract_address': None,
            'fn_name': name,
            'gas_limit': None,
            'gas_price': None,
            'gas_used': None,
            'input': None,
            'logs': [],
            'nonce': None,
            'receiver': None,
            'sender': sender,
            'status': -1,
            'txid': txid,
            'txindex': None,
            'value': None
        })
        if revert:
            self._revert_pc = revert[1]
            if revert[0]:
                # revert message was returned
                self.revert_msg = revert[0]
            else:
                # check for revert message as comment
                revert = build.get_dev_revert(revert[1])
                if type(revert) is str:
                    self.revert_msg = revert
        t = threading.Thread(
            target=self._await_confirm,
            args=[silent, callback],
            daemon=True
        )
        t.start()
        try:
            t.join()
            if ARGV['cli'] == "console":
                return
            if ARGV['coverage']:
                self._evaluate_trace()
            if not self.status:
                if revert is None:
                    # no revert message and unable to check dev string - have to get trace
                    self._evaluate_trace()
                raise VirtualMachineError({
                    "message": "revert "+(self.revert_msg or ""),
                    "source": self.error(1)
                })
        except KeyboardInterrupt:
            if ARGV['cli'] != "console":
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
        if tx['to'] and _contracts.find(tx['to']) is not None:
            self.receiver = _contracts.find(tx['to'])
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
        if self.status:
            self.events = decode_logs(receipt['logs'])
        if self.fn_name:
            history._gas(self.fn_name, receipt['gasUsed'])
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
                    )
                )
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
        if attr not in {
            'events',
            'modified_state',
            'return_value',
            'revert_msg',
            'trace'
        }:
            raise AttributeError("'TransactionReceipt' object has no attribute '{}'".format(attr))
        if self.status == -1:
            return None
        if attr == "trace":
            self._evaluate_trace()
        elif self._trace is None:
            self._get_trace()
        return self.__dict__[attr]

    def _get_trace(self):
        '''Retrieves the stack trace via debug_traceTransaction, and finds the
        return value, revert message and event logs in the trace.'''
        if self._trace is not None:
            return
        self.return_value = None
        if 'revert_msg' not in self.__dict__:
            self.revert_msg = None
        self._trace = []
        if (self.input == "0x" and self.gas_used == 21000) or self.contract_address:
            self.modified_state = bool(self.contract_address)
            self.trace = []
            return
        trace = web3.providers[0].make_request('debug_traceTransaction', [self.txid, {}])
        if 'error' in trace:
            self.modified_state = None
            raise RPCRequestError(trace['error']['message'])
        self._trace = trace = trace['result']['structLogs']
        if self.status:
            # get return value
            self.modified_state = bool(next((i for i in trace if i['op'] == "SSTORE"), False))
            step = trace[-1]
            if step['op'] != "RETURN":
                return
            contract = self.contract_address or self.receiver
            if type(contract) is str:
                return
            data = _get_memory(step, -1)
            fn = getattr(contract, self.fn_name.split('.')[-1])
            self.return_value = fn.decode_abi(data)
            return
        # get revert message
        self.modified_state = False
        # get events from trace
        self.events = decode_trace(trace)
        if self.revert_msg is not None:
            return
        if trace[-1]['op'] == "REVERT" and int(trace[-1]['stack'][-2], 16):
            data = _get_memory(trace[-1], -1)[8:]
            self.revert_msg = to_string(data[8:])
            return
        self.revert_msg = build.get_dev_revert(trace[-1]['pc'])
        if self.revert_msg is None:
            self._evaluate_trace()
            trace = self.trace[-1]
            try:
                self.revert_msg = build.get(trace['contractName'])['pcMap'][trace['pc']]['dev']
            except KeyError:
                self.revert_msg = ""

    def _evaluate_trace(self):
        '''Adds the following attributes to each step of the stack trace:

        address: The address executing this contract.
        contractName: The name of the contract.
        fn: The name of the function.
        source: Start and end offset associated source code.
        jumpDepth: Number of jumps made since entering this contract. The
                   initial value is 0.'''
        if 'trace' in self.__dict__:
            return
        if self._trace is None:
            self._get_trace()
        self.trace = trace = self._trace
        if not trace or 'fn' in trace[0]:
            return
        contract = self.contract_address or self.receiver
        pc = contract._build['pcMap'][0]
        fn = self.fn_name
        last_map = {0: {
            'address': contract.address,
            'contract': contract,
            'fn': [fn],
            'jumpDepth': 0
        }}
        trace[0].update({
            'address': last_map[0]['address'],
            'contractName': last_map[0]['contract']._name,
            'fn': last_map[0]['fn'][-1],
            'jumpDepth': 0,
            'source': {
                'filename': pc['path'],
                'offset': pc['offset']
            }
        })
        for i in range(1, len(trace)):
            # if depth has increased, tx has called into a different contract
            if trace[i]['depth'] > trace[i-1]['depth']:
                address = web3.toChecksumAddress(trace[i-1]['stack'][-2][-40:])
                contract = _contracts.find(address)
                stack_idx = -4 if trace[i-1]['op'] in {'CALL', 'CALLCODE'} else -3
                memory_idx = int(trace[i-1]['stack'][stack_idx], 16) * 2
                sig = "0x" + "".join(trace[i-1]['memory'])[memory_idx:memory_idx+8]
                pc = contract._build['pcMap'][trace[i]['pc']]
                fn = sources.get_contract_name(pc['path'], pc['offset'])
                fn += "."+(contract.get_method(sig) or "")
                last_map[trace[i]['depth']] = {
                    'address': address,
                    'contract': contract,
                    'fn': [fn],
                    'jumpDepth': 0
                    }
            last = last_map[trace[i]['depth']]
            contract = last['contract']
            trace[i].update({
                'address': last['address'],
                'contractName': contract._name,
                'fn': last['fn'][-1],
                'jumpDepth': last['jumpDepth'],
                'source': False
            })
            pc = contract._build['pcMap'][trace[i]['pc']]
            if 'path' in pc:
                trace[i]['source'] = {
                    'filename': pc['path'],
                    'offset': pc['offset']
                }
            if 'jump' not in pc or 'fn' not in pc:
                continue
            # jump 'i' is moving into an internal function
            if pc['jump'] == 'i':
                try:
                    last['fn'].append(contract._build['pcMap'][trace[i+1]['pc']]['fn'])
                    last['jumpDepth'] += 1
                except KeyError:
                    continue
            # jump 'o' is coming out of an internal function
            elif pc['jump'] == "o" and last['jumpDepth'] > 0:
                del last['fn'][-1]
                last['jumpDepth'] -= 1

    def info(self):
        '''Displays verbose information about the transaction, including
        decoded event logs.'''
        if self.contract_address:
            line = "New Contract Address{0}: {0[value]}{1}".format(color, self.contract_address)
        else:
            line = "To{0}: {0[value]}{1.receiver}{0}\n{0[key]}Value{0}: {0[value]}{1.value}".format(
                color, self
            )
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
                print("   "+color('bright yellow')+event.name+color())
                for k, v in event.items():
                    print("      {0[key]}{1}{0}: {0[value]}{2}{0}".format(
                        color, k, v
                    ))
            print()

    def call_trace(self):
        '''Displays the complete sequence of contracts and methods called during
        the transaction, and the range of trace step indexes for each method.

        Lines highlighed in red ended with a revert.'''
        trace = self.trace
        if not trace:
            if not self.contract_address:
                return ""
            raise NotImplementedError("Call trace is not available for deployment transactions.")
        result = "Call trace for '{0[value]}{1}{0}':\n".format(color, self.txid)
        indent = {0: 0}
        result += _step_print(trace[0], trace[-1], 0, 0, len(trace))
        trace_index = [(0, 0, 0)]+[
            (i, trace[i]['depth'], trace[i]['jumpDepth'])
            for i in range(1, len(trace)) if not _step_compare(trace[i], trace[i-1])
        ]
        for i, (idx, depth, jump_depth) in enumerate(trace_index[1:], start=1):
            last = trace_index[i-1]
            if depth > last[1]:
                indent[depth] = trace[idx-1]['jumpDepth'] + indent[depth-1]
                end = next((x[0] for x in trace_index[i+1:] if x[1] < depth), len(trace))
                result += _step_print(trace[idx], trace[end-1], depth+indent[depth], idx, end)
            elif depth == last[1] and jump_depth > last[2]:
                end = next(
                    (x[0] for x in trace_index[i+1:] if x[1] == depth and x[2] < jump_depth),
                    len(trace)
                )
                _depth = depth+jump_depth+indent[depth]
                result += _step_print(trace[idx], trace[end-1], _depth, idx, end)

    def traceback(self):
        '''Returns an error traceback for the transaction.'''
        if self.status == 1:
            return ""
        trace = self.trace
        if not trace:
            if not self.contract_address:
                return ""
            raise NotImplementedError("Traceback is not available for deployment transactions.")
        try:
            trace_range = range(len(trace)-1, -1, -1)
            idx = next(i for i in trace_range if trace[i]['op'] in {"REVERT", "INVALID"})
        except StopIteration:
            return ""

        result = [next(i for i in trace_range if trace[i]['source'])]
        depth, jump_depth = trace[idx]['depth'], trace[idx]['jumpDepth']

        while True:
            try:
                idx = next(
                    i for i in trace_range if trace[i]['depth'] < depth or
                    (trace[i]['depth'] == depth and trace[i]['jumpDepth'] < jump_depth)
                )
                result.append(idx)
                depth, jump_depth = trace[idx]['depth'], trace[idx]['jumpDepth']
            except StopIteration:
                break

        return (
            "Traceback for '{0[value]}{1}{0}':\n".format(color, self.txid) +
            "\n".join(self.source(i, 0) for i in result[::-1])
        )

    def error(self, pad=3):
        '''Returns the source code that caused the transaction to revert.

        Args:
            pad: Number of unrelated lines of code to include before and after

        Returns: source code string'''
        if self.status == 1:
            return ""
        if self._revert_pc:
            error = build.get_error_source_from_pc(self._revert_pc)
            if error:
                return _format_source(error, self._revert_pc, -1)
            self._revert_pc = None
        trace = self.trace
        trace_range = range(len(trace)-1, -1, -1)
        idx = next((i for i in trace_range if trace[i]['op'] in {"REVERT", "INVALID"}), -1)
        while idx >= 0:
            source = trace[idx]['source']
            if source and sources.get_fn(source['filename'], source['offset']) == trace[idx]['fn']:
                return self.source(idx)
            idx -= 1
        return ""

    def source(self, idx, pad=3):
        '''Displays the associated source code for a given stack trace step.

        Args:
            idx: Stack trace step index
            pad: Number of unrelated lines of code to include before and after

        Returns: source code string'''
        source = self.trace[idx]['source']
        if not source:
            return ""
        source = sources.get_highlighted_source(source['filename'], source['offset'], pad)
        return _format_source(source, self.trace[idx]['pc'], idx)


def _format_source(source, pc, idx):
    return (
        '{0[dull]}Trace step {0[value]}{1}{0[dull]}, program counter {0[value]}{2}{0[dull]}:'
        '\n  File {0[string]}"{3[1]}"{0[dull]}, line {0[value]}{3[2]}{0[dull]}, in '
        '{0[callable]}{3[3]}{0[dull]}:{3[0]}'
    ).format(color, idx, pc, source)


def _step_compare(a, b):
    return a['depth'] == b['depth'] and a['jumpDepth'] == b['jumpDepth']


def _step_print(step, last_step, indent, start, stop):
    print_str = "  "*indent + color('dull')
    if indent:
        print_str += "\u221f "
    if last_step['op'] in {"REVERT", "INVALID"} and _step_compare(step, last_step):
        contract_color = color("error")
    else:
        contract_color = color("contract" if not step['jumpDepth'] else "contract_method")
    print_str += "{1}{2} {0[dull]}{3}:{4}{0}".format(
        color, contract_color, step['fn'], start, stop
    )
    if not step['jumpDepth']:
        print_str += "  {0[dull]}({0}{1}{0[dull]}){0}".format(color, step['address'])
    return print_str


def _get_memory(step, idx):
    offset = int(step['stack'][idx], 16) * 2
    length = int(step['stack'][idx-1], 16) * 2
    return HexBytes("".join(step['memory'])[offset:offset+length]).hex()
