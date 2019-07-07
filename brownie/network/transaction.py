#!/usr/bin/python3

from hashlib import sha1
import threading
import time

from eth_abi import decode_abi
from hexbytes import HexBytes

from .history import (
    TxHistory,
    _ContractHistory
)
from .event import (
    decode_logs,
    decode_trace
)
from .web3 import Web3
from brownie.cli.utils import color
from brownie.exceptions import RPCRequestError, VirtualMachineError
from brownie.project import build, sources
from brownie.test import coverage
from brownie._config import ARGV

history = TxHistory()
_contracts = _ContractHistory()
web3 = Web3()


class TransactionReceipt:

    '''Attributes and methods relating to a broadcasted transaction.

    * All ether values are given as integers denominated in wei.
    * Before the tx has confirmed, most attributes are set to None
    * Accessing methods / attributes that query debug_traceTransaction
      may be very slow if the transaction involved many steps

    Attributes:
        contract_name: Name of the contract called in the transaction
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

    Additional attributes:
    (only available if debug_traceTransaction is enabled in the RPC)

        events: Decoded transaction log events
        trace: Expanded stack trace from debug_traceTransaction
        return_value: Return value(s) from contract call
        revert_msg: Error string from reverted contract all
        modified_state: Boolean, did this contract write to storage?'''

    def __init__(self, txid, sender=None, silent=False, name='', callback=None, revert=None):
        '''Instantiates a new TransactionReceipt object.

        Args:
            txid: hexstring transaction ID
            sender: sender as a hex string or Account object
            silent: toggles console verbosity
            name: contract function being called
            callback: optional callback function
            revert: (revert string, program counter)
        '''
        if type(txid) is not str:
            txid = txid.hex()
        if not silent:
            print(f"\n{color['key']}Transaction sent{color}: {color['value']}{txid}{color}")
        history._add_tx(self)

        self._trace = None
        self._revert_pc = None
        self.block_number = None
        self.contract_address = None
        self.gas_limit = None
        self.gas_price = None
        self.gas_used = None
        self.input = None
        self.logs = []
        self.nonce = None
        self.receiver = None
        self.sender = sender
        self.status = -1
        self.txid = txid
        self.txindex = None
        self.value = None

        self.contract_name = None
        self.fn_name = name
        if name and '.' in name:
            self.contract_name, self.fn_name = name.split('.', maxsplit=1)

        # avoid querying the trace to get the revert string if possible
        if revert:
            self._revert_pc = revert[1]
            if revert[0]:
                # revert message was returned
                self.revert_msg = revert[0]
            elif revert[2] == "revert":
                # check for dev revert string as a comment
                revert[0] = build.get_dev_revert(revert[1])
                if type(revert[0]) is str:
                    self.revert_msg = revert[0]

        # threaded to allow impatient users to ctrl-c to stop waiting in the console
        confirm_thread = threading.Thread(
            target=self._await_confirmation,
            args=(silent, callback),
            daemon=True
        )
        confirm_thread.start()
        try:
            confirm_thread.join()
            if ARGV['cli'] == "console":
                return
            # if coverage evaluation is active, evaluate the trace
            if ARGV['coverage'] and self.coverage_hash not in coverage and self.trace:
                self._expand_trace()
                coverage[self.coverage_hash] = self._coverage_eval
            if not self.status:
                if revert[0] is None:
                    # no revert message and unable to check dev string - have to get trace
                    self._expand_trace()
                raise VirtualMachineError({
                    "message": f"{revert[2]} {self.revert_msg or ''}",
                    "source": self._traceback_string() if ARGV['revert'] else self._error_string(1)
                })
        except KeyboardInterrupt:
            if ARGV['cli'] != "console":
                raise

    def __repr__(self):
        c = {-1: 'pending', 0: 'error', 1: None}
        return f"<Transaction object '{color[c[self.status]]}{self.txid}{color}'>"

    def __hash__(self):
        return hash(self.txid)

    def __getattr__(self, attr):
        # these values require debug_traceTransaction, only request it from the RPC when needed
        if attr not in {'events', 'modified_state', 'return_value', 'revert_msg', 'trace'}:
            raise AttributeError(f"'TransactionReceipt' object has no attribute '{attr}'")
        if self.status == -1:
            return None
        if attr == "trace":
            self._expand_trace()
        elif self._trace is None:
            self._get_trace()
        return self.__dict__[attr]

    def _await_confirmation(self, silent, callback):

        # await tx showing in mempool
        while True:
            tx = web3.eth.getTransaction(self.txid)
            if tx:
                break
            time.sleep(0.5)
        self._set_from_tx(tx)

        if not tx['blockNumber'] and not silent:
            print("Waiting for confirmation...")

        # await confirmation
        receipt = web3.eth.waitForTransactionReceipt(self.txid, None)
        self._set_from_receipt(receipt)
        if not silent:
            print(self._confirm_output())
        if callback:
            callback(self)

    def _set_from_tx(self, tx):
        if not self.sender:
            self.sender = tx['from']
        self.receiver = tx['to']
        self.value = tx['value']
        self.gas_price = tx['gasPrice']
        self.gas_limit = tx['gas']
        self.input = tx['input']
        self.nonce = tx['nonce']

        # if receiver is a known contract, set function name
        if tx['to'] and _contracts.find(tx['to']) is not None:
            self.receiver = _contracts.find(tx['to'])
            if not self.fn_name:
                self.contract_name = self.receiver._name
                self.fn_name = self.receiver.get_method(tx['input'])

    def _set_from_receipt(self, receipt):
        '''Sets object attributes based on the transaction reciept.'''
        self.block_number = receipt['blockNumber']
        self.txindex = receipt['transactionIndex']
        self.gas_used = receipt['gasUsed']
        self.contract_address = receipt['contractAddress']
        self.logs = receipt['logs']
        self.status = receipt['status']

        base = (
            f"{self.nonce}{self.block_number}{self.sender}{self.receiver}"
            f"{self.value}{self.input}{self.status}{self.gas_used}{self.txindex}"
        )
        self.coverage_hash = sha1(base.encode()).hexdigest()

        if self.status:
            self.events = decode_logs(receipt['logs'])
        if self.fn_name:
            history._gas(self._full_name(), receipt['gasUsed'])

    def _confirm_output(self):
        status = ""
        if not self.status:
            status = f"({color['error']}{self.revert_msg or 'reverted'}{color}) "
        result = (
            f"{self._full_name()} confirmed {status}- "
            f"{color['key']}block{color}: {color['value']}{self.block_number}{color}   "
            f"{color['key']}gas used{color}: {color['value']}{self.gas_used}{color} "
            f"({color['value']}{self.gas_used / self.gas_limit:.2%}{color})"
        )
        if self.contract_address:
            result += (
                f"\n{self.contract_name} deployed at: "
                f"{color['value']}{self.contract_address}{color}"
            )
        return result

    def _get_trace(self):
        '''Retrieves the stack trace via debug_traceTransaction and finds the
        return value, revert message and event logs in the trace.
        '''

        # check if trace has already been retrieved, or the tx warrants it
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

        trace = web3.providers[0].make_request(
            'debug_traceTransaction',
            (self.txid, {'disableStorage': ARGV['cli'] != "console"})
        )

        if 'error' in trace:
            self.modified_state = None
            raise RPCRequestError(trace['error']['message'])
        self._trace = trace = trace['result']['structLogs']
        if not trace:
            self.modified_state = False
        elif self.status:
            self._confirmed_trace(trace)
        else:
            self._reverted_trace(trace)

    def _confirmed_trace(self, trace):
        self.modified_state = next((True for i in trace if i['op'] == "SSTORE"), False)
        step = trace[-1]
        if step['op'] != "RETURN" or type(self.receiver) is str:
            return
        # get return value
        data = _get_memory(step, -1)
        fn = getattr(self.receiver, self.fn_name)
        self.return_value = fn.decode_abi(data)
        return

    def _reverted_trace(self, trace):
        self.modified_state = False
        # get events from trace
        self.events = decode_trace(trace)
        if self.revert_msg is not None:
            return
        # get revert message
        step = next(i for i in trace if i['op'] in ("REVERT", "INVALID"))
        if step['op'] == "REVERT" and int(step['stack'][-2], 16):
            # get returned error string from stack
            data = _get_memory(step, -1)[4:]
            self.revert_msg = decode_abi(['string'], data)[0].decode()
            return
        # check for dev revert string using program counter
        self.revert_msg = build.get_dev_revert(step['pc'])
        if self.revert_msg is not None:
            return
        # if none is found, expand the trace and get it from the pcMap
        self._expand_trace()
        try:
            pc_map = build.get(step['contractName'])['pcMap']
            # if this is the function selector revert, check for a jump
            if 'first_revert' in pc_map[step['pc']]:
                i = trace.index(step) - 4
                if trace[i]['pc'] != step['pc'] - 4:
                    step = trace[i]
            self.revert_msg = pc_map[step['pc']]['dev']
        except KeyError:
            self.revert_msg = ""

    def _expand_trace(self):
        '''Adds the following attributes to each step of the stack trace:

        address: The address executing this contract.
        contractName: The name of the contract.
        fn: The name of the function.
        jumpDepth: Number of jumps made since entering this contract. The
                   initial value is 0.
        source: {
            filename: path to the source file for this step
            offset: Start and end offset associated source code
        }
        '''

        if 'trace' in self.__dict__:
            return
        if self._trace is None:
            self._get_trace()
        self.trace = trace = self._trace
        if not trace or 'fn' in trace[0]:
            self._coverage_eval = {}
            return

        # last_map gives a quick reference of previous values at each depth
        last_map = {0: {
            'address': self.receiver.address,
            'contract': self.receiver,
            'name': self.receiver._name,
            'fn': [self._full_name()],
            'jumpDepth': 0,
            'pc_map': self.receiver._build['pcMap']
        }}

        coverage_eval = {self.receiver._name: {}}
        active_branches = set()

        for i in range(len(trace)):
            # if depth has increased, tx has called into a different contract
            if trace[i]['depth'] > trace[i-1]['depth']:
                # get call signature
                stack_idx = -4 if trace[i-1]['op'] in {'CALL', 'CALLCODE'} else -3
                offset = int(trace[i-1]['stack'][stack_idx], 16) * 2
                sig = HexBytes("".join(trace[i-1]['memory'])[offset:offset+8]).hex()

                # get contract and method name
                address = web3.toChecksumAddress(trace[i-1]['stack'][-2][-40:])
                contract = _contracts.find(address)

                # update last_map
                last_map[trace[i]['depth']] = {
                    'address': address,
                    'contract': contract,
                    'name': contract._name,
                    'fn': [f"{contract._name}.{contract.get_method(sig)}"],
                    'jumpDepth': 0,
                    'pc_map': contract._build['pcMap']
                }
                if contract._name not in coverage_eval:
                    coverage_eval[contract._name] = {}

            # update trace from last_map
            last = last_map[trace[i]['depth']]
            trace[i].update({
                'address': last['address'],
                'contractName': last['name'],
                'fn': last['fn'][-1],
                'jumpDepth': last['jumpDepth'],
                'source': False
            })
            pc = last['pc_map'][trace[i]['pc']]
            if 'path' not in pc:
                continue

            trace[i]['source'] = {'filename': pc['path'], 'offset': pc['offset']}

            if 'fn' not in pc:
                continue

            # calculate coverage
            if '<string' not in pc['path']:
                if pc['path'] not in coverage_eval[last['name']]:
                    coverage_eval[last['name']][pc['path']] = [set(), set(), set()]
                if 'statement' in pc:
                    coverage_eval[last['name']][pc['path']][0].add(pc['statement'])
                if 'branch' in pc:
                    if pc['op'] != "JUMPI":
                        active_branches.add(pc['branch'])
                    elif pc['branch'] in active_branches:
                        # false, true
                        key = 1 if trace[i+1]['pc'] == trace[i]['pc']+1 else 2
                        coverage_eval[last['name']][pc['path']][key].add(pc['branch'])
                        active_branches.remove(pc['branch'])

            # ignore jumps with no function - they are compiler optimizations
            if 'jump' not in pc:
                continue

            # jump 'i' is calling into an internal function
            if pc['jump'] == 'i':
                try:
                    last['fn'].append(last['pc_map'][trace[i+1]['pc']]['fn'])
                    last['jumpDepth'] += 1
                except KeyError:
                    continue
            # jump 'o' is returning from an internal function
            elif pc['jump'] == "o" and last['jumpDepth'] > 0:
                del last['fn'][-1]
                last['jumpDepth'] -= 1
        self._coverage_eval = dict((k, v) for k, v in coverage_eval.items() if v)

    def _full_name(self):
        if self.contract_name:
            return f"{self.contract_name}.{self.fn_name}"
        return self.fn_name or "Transaction"

    def info(self):
        '''Displays verbose information about the transaction, including decoded event logs.'''
        status = ""
        if not self.status:
            status = f"({color['error']}{self.revert_msg or 'reverted'}{color})"

        result = (
            f"Transaction was Mined {status}\n---------------------\n"
            f"{color['key']}Tx Hash{color}: {color['value']}{self.txid}\n"
            f"{color['key']}From{color}: {color['value']}{self.sender}\n"
        )

        if self.contract_address:
            result += (
                f"{color['key']}New {self.contract_name} address{color}: "
                f"{color['value']}{self.contract_address}\n"
            )
        else:
            result += (
                f"{color['key']}To{color}: {color['value']}{self.receiver}{color}\n"
                f"{color['key']}Value{color}: {color['value']}{self.value}\n"
            )
            if int(self.input, 16):
                result += f"{color['key']}Function{color}: {color['value']}{self._full_name()}\n"

        result += (
            f"{color['key']}Block{color}: {color['value']}{self.block_number}{color}\n"
            f"{color['key']}Gas Used{color}: "
            f"{color['value']}{self.gas_used}{color} / {color['value']}{self.gas_limit}{color} "
            f"({color['value']}{self.gas_used / self.gas_limit:.1%}{color})\n"
        )

        if self.events:
            result += "\n   Events In This Transaction\n   --------------------------"
            for event in self.events:
                result += f"\n   {color['bright yellow']}{event.name}{color}"
                for key, value in event.items():
                    result += f"\n      {color['key']}{key}{color}: {color['value']}{value}{color}"
        print(result)

    def call_trace(self):
        '''Displays the complete sequence of contracts and methods called during
        the transaction, and the range of trace step indexes for each method.

        Lines highlighed in red ended with a revert.
        '''
        trace = self.trace
        if not trace:
            if not self.contract_address:
                return
            raise NotImplementedError("Call trace is not available for deployment transactions.")

        result = f"Call trace for '{color['value']}{self.txid}{color}':"
        result += _step_print(trace[0], trace[-1], 0, 0, len(trace))
        indent = {0: 0}

        # (index, depth, jumpDepth) for relevent steps in the trace
        trace_index = [(0, 0, 0)] + [
            (i, trace[i]['depth'], trace[i]['jumpDepth'])
            for i in range(1, len(trace)) if not _step_compare(trace[i], trace[i-1])
        ]

        for i, (idx, depth, jump_depth) in enumerate(trace_index[1:], start=1):
            last = trace_index[i-1]
            if depth > last[1]:
                # called to a new contract
                indent[depth] = trace[idx-1]['jumpDepth'] + indent[depth-1]
                end = next((x[0] for x in trace_index[i+1:] if x[1] < depth), len(trace))
                result += _step_print(trace[idx], trace[end-1], depth+indent[depth], idx, end)
            elif depth == last[1] and jump_depth > last[2]:
                # jumped into an internal function
                end = next((
                    x[0] for x in trace_index[i+1:] if x[1] < depth or
                    (x[1] == depth and x[2] < jump_depth)
                ), len(trace))
                _depth = depth+jump_depth+indent[depth]
                result += _step_print(trace[idx], trace[end-1], _depth, idx, end)
        print(result)

    def traceback(self):
        print(self._traceback_string())

    def _traceback_string(self):
        '''Returns an error traceback for the transaction.'''
        if self.status == 1:
            return ""
        trace = self.trace
        if not trace:
            if not self.contract_address:
                return ""
            raise NotImplementedError("Traceback is not available for deployment transactions.")

        try:
            idx = next(i for i in range(len(trace)) if trace[i]['op'] in ("REVERT", "INVALID"))
            trace_range = range(idx, -1, -1)
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
            f"{color}Traceback for '{color['value']}{self.txid}{color}':\n" +
            "\n".join(self._source_string(i, 0) for i in result[::-1])
        )

    def error(self, pad=3):
        print(self._error_string(pad))

    def _error_string(self, pad=3):
        '''Returns the source code that caused the transaction to revert.

        Args:
            pad: Number of unrelated lines of code to include before and after

        Returns: source code string
        '''
        if self.status == 1:
            return ""

        # if RPC returned a program counter, try to find source without querying trace
        if self._revert_pc:
            error, fn_name = build.get_error_source_from_pc(self._revert_pc)
            if error:
                return _format_source(error, self._revert_pc, -1, fn_name)
            self._revert_pc = None

        # iterate backward through the trace until a step has a source offset
        trace = self.trace
        trace_range = range(len(trace)-1, -1, -1)
        try:
            idx = next(i for i in trace_range if trace[i]['op'] in {"REVERT", "INVALID"})
            idx = next(i for i in trace_range if trace[i]['source'])
            return self._source_string(idx, pad)
        except StopIteration:
            return ""

    def source(self, idx, pad=3):
        print(self._source_string(idx, pad))

    def _source_string(self, idx, pad):
        '''Displays the associated source code for a given stack trace step.

        Args:
            idx: Stack trace step index
            pad: Number of unrelated lines of code to include before and after

        Returns: source code string
        '''
        source = self.trace[idx]['source']
        if not source:
            return ""
        source = sources.get_highlighted_source(source['filename'], source['offset'], pad)
        return _format_source(source, self.trace[idx]['pc'], idx, self.trace[idx]['fn'])


def _format_source(source, pc, idx, fn_name):
    ln = f" {color['value']}{source[2][0]}"
    if source[2][1] > source[2][0]:
        ln = f"s{ln}{color['dull']}-{color['value']}{source[2][1]}"
    return (
        f"{color['dull']}Trace step {color['value']}{idx}{color['dull']}, "
        f"program counter {color['value']}{pc}{color['dull']}:\n  {color['dull']}"
        f"File {color['string']}\"{source[1]}\"{color['dull']}, line{ln}{color['dull']},"
        f" in {color['callable']}{fn_name}{color['dull']}:{source[0]}"
    )


def _step_compare(a, b):
    return a['depth'] == b['depth'] and a['jumpDepth'] == b['jumpDepth']


def _step_print(step, last_step, indent, start, stop):
    print_str = f"\n{'  '*indent}{color['dull']}"
    if indent:
        print_str += "\u221f "
    if last_step['op'] in {"REVERT", "INVALID"} and _step_compare(step, last_step):
        contract_color = color("error")
    else:
        contract_color = color("contract_method" if not step['jumpDepth'] else "")
    print_str += f"{contract_color}{step['fn']} {color['dull']}{start}:{stop}{color}"
    if not step['jumpDepth']:
        print_str += f"  {color['dull']}({color}{step['address']}{color['dull']}){color}"
    return print_str


def _get_memory(step, idx):
    offset = int(step['stack'][idx], 16) * 2
    length = int(step['stack'][idx-1], 16) * 2
    return HexBytes("".join(step['memory'])[offset:offset+length])
