#!/usr/bin/python3

import threading
import time
from hashlib import sha1
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import requests
from eth_abi import decode_abi
from hexbytes import HexBytes
from web3.exceptions import TransactionNotFound

from brownie._config import ARGV
from brownie.convert import EthAddress, Wei
from brownie.exceptions import RPCRequestError, VirtualMachineError
from brownie.project import build
from brownie.project.sources import highlight_source
from brownie.test import coverage
from brownie.utils import color

from .event import _decode_logs, _decode_trace
from .state import TxHistory, _find_contract
from .web3 import web3

__tracebackhide__ = True
history = TxHistory()


def trace_property(fn: Callable) -> Any:
    # attributes that are only available after querying the tranasaction trace

    @property  # type: ignore
    def wrapper(self: "TransactionReceipt") -> Any:
        if self.status == -1:
            return None
        return fn(self)

    return wrapper


def trace_inspection(fn: Callable) -> Any:
    def wrapper(self: "TransactionReceipt", *args: Any, **kwargs: Any) -> Any:
        if self.contract_address:
            raise NotImplementedError(
                "Trace inspection methods are not available for deployment transactions."
            )
        if self.input == "0x" and self.gas_used == 21000:
            return None
        return fn(self, *args, **kwargs)

    return wrapper


class TransactionReceipt:

    """Attributes and methods relating to a broadcasted transaction.

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
        modified_state: Boolean, did this contract write to storage?"""

    __slots__ = (
        "_confirmed",
        "_events",
        "_internal_transfers",
        "_modified_state",
        "_new_contracts",
        "_raw_trace",
        "_return_value",
        "_revert_msg",
        "_revert_pc",
        "_trace",
        "block_number",
        "contract_address",
        "contract_name",
        "coverage_hash",
        "fn_name",
        "gas_limit",
        "gas_price",
        "gas_used",
        "input",
        "logs",
        "nonce",
        "receiver",
        "sender",
        "status",
        "txid",
        "txindex",
        "value",
    )

    def __init__(
        self,
        txid: Union[str, bytes],
        sender: Any = None,
        silent: bool = False,
        name: str = "",
        revert_data: Optional[Tuple] = None,
    ) -> None:
        """Instantiates a new TransactionReceipt object.

        Args:
            txid: hexstring transaction ID
            sender: sender as a hex string or Account object
            silent: toggles console verbosity
            name: contract function being called
            revert_data: (revert string, program counter, revert type)
        """

        if ARGV["cli"] == "test":
            silent = True
        if isinstance(txid, bytes):
            txid = txid.hex()
        if not silent:
            print(f"Transaction sent: {color('bright blue')}{txid}{color}")
        history._add_tx(self)

        self._raw_trace = None
        self._trace = None
        self._events = None
        self._return_value = None
        self._revert_msg = None
        self._modified_state = None
        self._new_contracts = None
        self._internal_transfers = None
        self._confirmed = threading.Event()

        self.sender = sender
        self.status = -1
        self.txid = txid
        self.fn_name = name

        if name and "." in name:
            self.contract_name, self.fn_name = name.split(".", maxsplit=1)

        # avoid querying the trace to get the revert string if possible
        revert_msg, self._revert_pc, revert_type = revert_data or (None, None, None)
        if revert_msg:
            # revert message was returned
            self._revert_msg = revert_msg
        elif revert_type in ("revert", "invalid opcode"):
            # check for dev revert string as a comment
            self._revert_msg = build._get_dev_revert(self._revert_pc)
        else:
            self._revert_msg = revert_type

        # threaded to allow impatient users to ctrl-c to stop waiting in the console
        confirm_thread = threading.Thread(
            target=self._await_confirmation, args=(silent,), daemon=True
        )
        confirm_thread.start()
        try:
            confirm_thread.join()
            if ARGV["cli"] == "console":
                return
            # if coverage evaluation is active, evaluate the trace
            if ARGV["coverage"] and not coverage._check_cached(self.coverage_hash) and self.trace:
                self._expand_trace()
            if not self.status:
                if self._revert_msg is None:
                    # no revert message and unable to check dev string - have to get trace
                    self._expand_trace()
                if self.contract_address:
                    source = ""
                else:
                    source = self._traceback_string() if ARGV["revert"] else self._error_string(1)
                raise VirtualMachineError({"message": self._revert_msg or "", "source": source})
        except KeyboardInterrupt:
            if ARGV["cli"] != "console":
                raise

    def __repr__(self) -> str:
        c = {-1: "bright yellow", 0: "bright red", 1: None}
        return f"<Transaction '{color(c[self.status])}{self.txid}{color}'>"

    def __hash__(self) -> int:
        return hash(self.txid)

    def __getattr__(self, attr: str) -> Any:
        if attr not in self.__slots__:
            raise AttributeError(f"'TransactionReceipt' object has no attribute '{attr}'")
        if self.status == -1:
            return None

    @trace_property
    def events(self) -> Optional[List]:
        if not self.status:
            self._get_trace()
        return self._events

    @trace_property
    def internal_transfers(self) -> Optional[List]:
        if not self.status:
            return []
        if self._internal_transfers is None:
            self._expand_trace()
        return self._internal_transfers

    @trace_property
    def modified_state(self) -> Optional[bool]:
        if not self.status:
            self._modified_state = False
        elif self._modified_state is None:
            self._get_trace()
        return self._modified_state

    @trace_property
    def new_contracts(self) -> Optional[List]:
        if not self.status:
            return []
        if self._new_contracts is None:
            self._expand_trace()
        return self._new_contracts

    @trace_property
    def return_value(self) -> Optional[str]:
        if not self.status:
            return None
        if self._return_value is None:
            self._get_trace()
        return self._return_value

    @trace_property
    def revert_msg(self) -> Optional[str]:
        if self.status:
            return None
        if self._revert_msg is None:
            self._get_trace()
        elif self.contract_address and self._revert_msg == "out of gas":
            self._get_trace()
        return self._revert_msg

    @trace_property
    def trace(self) -> Optional[List]:
        if self._trace is None:
            self._expand_trace()
        return self._trace

    def _await_confirmation(self, silent: bool) -> None:
        # await tx showing in mempool
        while True:
            try:
                tx = web3.eth.getTransaction(self.txid)
                break
            except TransactionNotFound:
                time.sleep(0.5)
        self._set_from_tx(tx)

        if not silent:
            print(
                f"  Gas price: {color('bright blue')}{self.gas_price/10**9}{color} gwei"
                f"   Gas limit: {color('bright blue')}{self.gas_limit}{color}"
            )
        if not tx["blockNumber"] and not silent:
            print("Waiting for confirmation...")

        # await confirmation
        receipt = web3.eth.waitForTransactionReceipt(self.txid, None)
        self._set_from_receipt(receipt)
        self._confirmed.set()
        if not silent:
            print(self._confirm_output())

    def _set_from_tx(self, tx: Dict) -> None:
        if not self.sender:
            self.sender = EthAddress(tx["from"])
        self.receiver = EthAddress(tx["to"]) if tx["to"] else None
        self.value = Wei(tx["value"])
        self.gas_price = tx["gasPrice"]
        self.gas_limit = tx["gas"]
        self.input = tx["input"]
        self.nonce = tx["nonce"]

        # if receiver is a known contract, set function name
        if not self.fn_name and _find_contract(tx["to"]) is not None:
            contract = _find_contract(tx["to"])
            self.contract_name = contract._name
            self.fn_name = contract.get_method(tx["input"])

    def _set_from_receipt(self, receipt: Dict) -> None:
        """Sets object attributes based on the transaction reciept."""
        self.block_number = receipt["blockNumber"]
        self.txindex = receipt["transactionIndex"]
        self.gas_used = receipt["gasUsed"]
        self.contract_address = receipt["contractAddress"]
        self.logs = receipt["logs"]
        self.status = receipt["status"]

        base = (
            f"{self.nonce}{self.block_number}{self.sender}{self.receiver}"
            f"{self.value}{self.input}{self.status}{self.gas_used}{self.txindex}"
        )
        self.coverage_hash = sha1(base.encode()).hexdigest()

        if self.status:
            self._events = _decode_logs(receipt["logs"])
        if self.fn_name:
            history._gas(self._full_name(), receipt["gasUsed"])

    def _confirm_output(self) -> str:
        status = ""
        if not self.status:
            status = f"({color('bright red')}{self.revert_msg or 'reverted'}{color}) "
        result = (
            f"  {self._full_name()} confirmed {status}- "
            f"Block: {color('bright blue')}{self.block_number}{color}   "
            f"Gas used: {color('bright blue')}{self.gas_used}{color} "
            f"({color('bright blue')}{self.gas_used / self.gas_limit:.2%}{color})"
        )
        if self.status and self.contract_address:
            result += (
                f"\n  {self.contract_name} deployed at: "
                f"{color('bright blue')}{self.contract_address}{color}"
            )
        return result + "\n"

    def _get_trace(self) -> None:
        """Retrieves the stack trace via debug_traceTransaction and finds the
        return value, revert message and event logs in the trace.
        """

        # check if trace has already been retrieved, or the tx warrants it
        if self._raw_trace is not None:
            return
        self._raw_trace = []
        if self.input == "0x" and self.gas_used == 21000:
            self._modified_state = False
            self._trace = []
            return

        try:
            trace = web3.provider.make_request(  # type: ignore
                "debug_traceTransaction", (self.txid, {"disableStorage": ARGV["cli"] != "console"})
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            msg = f"Encountered a {type(e).__name__} while requesting "
            msg += "debug_traceTransaction. The local RPC client has likely crashed."
            if ARGV["coverage"]:
                msg += " If the error persists, add the skip_coverage fixture to this test."
            raise RPCRequestError(msg) from None

        if "error" in trace:
            self.modified_state = None
            raise RPCRequestError(trace["error"]["message"])
        self._raw_trace = trace = trace["result"]["structLogs"]
        if not trace:
            self._modified_state = False
        elif self.status:
            self._confirmed_trace(trace)
        else:
            self._reverted_trace(trace)

    def _confirmed_trace(self, trace: Sequence) -> None:
        self._modified_state = next((True for i in trace if i["op"] == "SSTORE"), False)

        if trace[-1]["op"] != "RETURN" or self.contract_address:
            return
        contract = _find_contract(self.receiver)
        if contract:
            data = _get_memory(trace[-1], -1)
            fn = getattr(contract, self.fn_name)
            self._return_value = fn.decode_output(data)

    def _reverted_trace(self, trace: Sequence) -> None:
        self._modified_state = False
        # get events from trace
        self._events = _decode_trace(trace)
        if self.contract_address:
            step = next((i for i in trace if i["op"] == "CODECOPY"), None)
            if step is not None and int(step["stack"][-3], 16) > 24577:
                self._revert_msg = "exceeds EIP-170 size limit"
        if self._revert_msg is not None:
            return
        # get revert message
        step = next(i for i in trace if i["op"] in ("REVERT", "INVALID"))
        if step["op"] == "REVERT" and int(step["stack"][-2], 16):
            # get returned error string from stack
            data = _get_memory(step, -1)[4:]
            self._revert_msg = decode_abi(["string"], data)[0]
            return
        if self.contract_address:
            self._revert_msg = "invalid opcode" if step["op"] == "INVALID" else ""
            return
        # check for dev revert string using program counter
        self._revert_msg = build._get_dev_revert(step["pc"])
        if self._revert_msg is not None:
            return
        # if none is found, expand the trace and get it from the pcMap
        self._expand_trace()
        try:
            pc_map = _find_contract(step["address"])._build["pcMap"]
            # if this is the function selector revert, check for a jump
            if "first_revert" in pc_map[step["pc"]]:
                i = trace.index(step) - 4
                if trace[i]["pc"] != step["pc"] - 4:
                    step = trace[i]
            self._revert_msg = pc_map[step["pc"]]["dev"]
        except (KeyError, AttributeError):
            self._revert_msg = "invalid opcode" if step["op"] == "INVALID" else ""

    def _expand_trace(self) -> None:
        """Adds the following attributes to each step of the stack trace:

        address: The address executing this contract.
        contractName: The name of the contract.
        fn: The name of the function.
        jumpDepth: Number of jumps made since entering this contract. The
                   initial value is 0.
        source: {
            filename: path to the source file for this step
            offset: Start and end offset associated source code
        }
        """
        if self._trace is not None:
            return
        if self._raw_trace is None:
            self._get_trace()
        self._trace = trace = self._raw_trace
        self._new_contracts = []
        self._internal_transfers = []
        if self.contract_address or not trace:
            coverage._add_transaction(self.coverage_hash, {})
            return
        if "fn" in trace[0]:
            return

        # last_map gives a quick reference of previous values at each depth
        last_map = {0: _get_last_map(self.receiver, self.input[:10])}  # type: ignore
        coverage_eval: Dict = {last_map[0]["name"]: {}}

        for i in range(len(trace)):
            # if depth has increased, tx has called into a different contract
            if trace[i]["depth"] > trace[i - 1]["depth"]:
                step = trace[i - 1]
                if step["op"] in ("CREATE", "CREATE2"):
                    # creating a new contract
                    out = next(x for x in trace[i:] if x["depth"] == step["depth"])
                    address = out["stack"][-1][-40:]
                    sig = f"<{step['op']}>"
                    self._new_contracts.append(EthAddress(address))
                    if int(step["stack"][-1], 16):
                        self._add_internal_xfer(step["address"], address, step["stack"][-1])
                else:
                    # calling an existing contract
                    stack_idx = -4 if step["op"] in ("CALL", "CALLCODE") else -3
                    offset = int(step["stack"][stack_idx], 16) * 2
                    sig = HexBytes("".join(step["memory"])[offset : offset + 8]).hex()
                    address = step["stack"][-2][-40:]

                last_map[trace[i]["depth"]] = _get_last_map(address, sig)
                coverage_eval.setdefault(last_map[trace[i]["depth"]]["name"], {})

            # update trace from last_map
            last = last_map[trace[i]["depth"]]
            trace[i].update(
                address=last["address"],
                contractName=last["name"],
                fn=last["fn"][-1],
                jumpDepth=last["jumpDepth"],
                source=False,
            )

            if trace[i]["op"] == "CALL" and int(trace[i]["stack"][-3], 16):
                self._add_internal_xfer(
                    last["address"], trace[i]["stack"][-2][-40:], trace[i]["stack"][-3]
                )

            if "pc_map" not in last:
                continue
            pc = last["pc_map"][trace[i]["pc"]]

            if "path" not in pc:
                continue
            trace[i]["source"] = {"filename": pc["path"], "offset": pc["offset"]}

            if "fn" not in pc:
                continue

            # calculate coverage
            if last["coverage"]:
                if pc["path"] not in coverage_eval[last["name"]]:
                    coverage_eval[last["name"]][pc["path"]] = [set(), set(), set()]
                if "statement" in pc:
                    coverage_eval[last["name"]][pc["path"]][0].add(pc["statement"])
                if "branch" in pc:
                    if pc["op"] != "JUMPI":
                        last["active_branches"].add(pc["branch"])
                    elif "active_branches" not in last or pc["branch"] in last["active_branches"]:
                        # false, true
                        key = 1 if trace[i + 1]["pc"] == trace[i]["pc"] + 1 else 2
                        coverage_eval[last["name"]][pc["path"]][key].add(pc["branch"])
                        if "active_branches" in last:
                            last["active_branches"].remove(pc["branch"])

            # ignore jumps with no function - they are compiler optimizations
            if "jump" in pc:
                # jump 'i' is calling into an internal function
                if pc["jump"] == "i":
                    try:
                        fn = last["pc_map"][trace[i + 1]["pc"]]["fn"]
                    except (KeyError, IndexError):
                        continue
                    if fn != last["fn"][-1]:
                        last["fn"].append(fn)
                        last["jumpDepth"] += 1
                # jump 'o' is returning from an internal function
                elif last["jumpDepth"] > 0:
                    del last["fn"][-1]
                    last["jumpDepth"] -= 1
        coverage._add_transaction(
            self.coverage_hash, dict((k, v) for k, v in coverage_eval.items() if v)
        )

    def _add_internal_xfer(self, from_: str, to: str, value: str) -> None:
        self._internal_transfers.append(  # type: ignore
            {"from": EthAddress(from_), "to": EthAddress(to), "value": Wei(f"0x{value}")}
        )

    def _full_name(self) -> str:
        if self.contract_name and self.fn_name:
            return f"{self.contract_name}.{self.fn_name}"
        return self.fn_name or "Transaction"

    def info(self) -> None:
        """Displays verbose information about the transaction, including decoded event logs."""
        status = ""
        if not self.status:
            status = f"({color('bright red')}{self.revert_msg or 'reverted'}{color})"

        result = (
            f"Transaction was Mined {status}\n---------------------\n"
            f"Tx Hash: {color('bright blue')}{self.txid}\n"
            f"From: {color('bright blue')}{self.sender}\n"
        )

        if self.contract_address and self.status:
            result += (
                f"New {self.contract_name} address: {color('bright blue')}{self.contract_address}\n"
            )
        else:
            result += (
                f"To: {color('bright blue')}{self.receiver}{color}\n"
                f"Value: {color('bright blue')}{self.value}\n"
            )
            if self.input != "0x" and int(self.input, 16):
                result += f"Function: {color('bright blue')}{self._full_name()}\n"

        result += (
            f"Block: {color('bright blue')}{self.block_number}{color}\nGas Used: "
            f"{color('bright blue')}{self.gas_used}{color} / {color('bright blue')}{self.gas_limit}"
            f"{color} ({color('bright blue')}{self.gas_used / self.gas_limit:.1%}{color})\n"
        )

        if self.events:
            result += "\n   Events In This Transaction\n   --------------------------"
            for event in self.events:  # type: ignore
                result += f"\n   {color('bright yellow')}{event.name}{color}"  # type: ignore
                for key, value in event.items():  # type: ignore
                    result += f"\n      {key}: {color('bright blue')}{value}{color}"
        print(result)

    @trace_inspection
    def call_trace(self) -> None:
        """Displays the complete sequence of contracts and methods called during
        the transaction, and the range of trace step indexes for each method.

        Lines highlighed in red ended with a revert.
        """

        trace = self.trace
        result = f"Call trace for '{color('bright blue')}{self.txid}{color}':"
        result += _step_print(trace[0], trace[-1], None, 0, len(trace))
        indent = {0: 0}
        indent_chars = [""] * 1000

        # (index, depth, jumpDepth) for relevent steps in the trace
        trace_index = [(0, 0, 0)] + [
            (i, trace[i]["depth"], trace[i]["jumpDepth"])
            for i in range(1, len(trace))
            if not _step_compare(trace[i], trace[i - 1])
        ]

        for i, (idx, depth, jump_depth) in enumerate(trace_index[1:], start=1):
            last = trace_index[i - 1]
            if depth > last[1]:
                # called to a new contract
                indent[depth] = trace_index[i - 1][2] + indent[depth - 1]
                end = next((x[0] for x in trace_index[i + 1 :] if x[1] < depth), len(trace))
                _depth = depth + indent[depth]
                symbol, indent_chars[_depth] = _check_last(trace_index[i - 1 :])
                indent_str = "".join(indent_chars[:_depth]) + symbol
                result += _step_print(trace[idx], trace[end - 1], indent_str, idx, end)
            elif depth == last[1] and jump_depth > last[2]:
                # jumped into an internal function
                end = next(
                    (
                        x[0]
                        for x in trace_index[i + 1 :]
                        if x[1] < depth or (x[1] == depth and x[2] < jump_depth)
                    ),
                    len(trace),
                )
                _depth = depth + jump_depth + indent[depth]
                symbol, indent_chars[_depth] = _check_last(trace_index[i - 1 :])
                indent_str = "".join(indent_chars[:_depth]) + symbol
                result += _step_print(trace[idx], trace[end - 1], indent_str, idx, end)
        print(result)

    def traceback(self) -> None:
        print(self._traceback_string() or "")

    @trace_inspection
    def _traceback_string(self) -> str:
        """Returns an error traceback for the transaction."""
        if self.status == 1:
            return ""
        trace = self.trace

        try:
            idx = next(i for i in range(len(trace)) if trace[i]["op"] in ("REVERT", "INVALID"))
            trace_range = range(idx, -1, -1)
        except StopIteration:
            return ""

        result = [next(i for i in trace_range if trace[i]["source"])]
        depth, jump_depth = trace[idx]["depth"], trace[idx]["jumpDepth"]

        while True:
            try:
                idx = next(
                    i
                    for i in trace_range
                    if trace[i]["depth"] < depth
                    or (trace[i]["depth"] == depth and trace[i]["jumpDepth"] < jump_depth)
                )
                result.append(idx)
                depth, jump_depth = trace[idx]["depth"], trace[idx]["jumpDepth"]
            except StopIteration:
                break
        return f"{color}Traceback for '{color('bright blue')}{self.txid}{color}':\n" + "\n".join(
            self._source_string(i, 0) for i in result[::-1]
        )

    def error(self, pad: int = 3) -> None:
        print(self._error_string(pad) or "")

    @trace_inspection
    def _error_string(self, pad: int = 3) -> str:
        """Returns the source code that caused the transaction to revert.

        Args:
            pad: Number of unrelated lines of code to include before and after

        Returns: source code string
        """
        if self.status == 1:
            return ""

        # if RPC returned a program counter, try to find source without querying trace
        if self._revert_pc:
            highlight, linenos, path, fn_name = build._get_error_source_from_pc(self._revert_pc)
            if highlight:
                return _format_source(highlight, linenos, path, self._revert_pc, -1, fn_name)
            self._revert_pc = None

        # iterate backward through the trace until a step has a source offset
        trace = self.trace
        trace_range = range(len(trace) - 1, -1, -1)
        try:
            idx = next(i for i in trace_range if trace[i]["op"] in {"REVERT", "INVALID"})
            idx = next(i for i in trace_range if trace[i]["source"])
            return self._source_string(idx, pad)
        except StopIteration:
            return ""

    def source(self, idx: int, pad: int = 3) -> None:
        print(self._source_string(idx, pad) or "")

    @trace_inspection
    def _source_string(self, idx: int, pad: int) -> str:
        """Displays the associated source code for a given stack trace step.

        Args:
            idx: Stack trace step index
            pad: Number of unrelated lines of code to include before and after

        Returns: source code string
        """
        trace = self.trace[idx]
        if not trace.get("source", None):
            return ""
        contract = _find_contract(self.trace[idx]["address"])
        source, linenos = highlight_source(
            contract._project._sources.get(trace["source"]["filename"]),
            trace["source"]["offset"],
            pad,
        )
        if not source:
            return ""
        return _format_source(
            source,
            linenos,
            trace["source"]["filename"],
            trace["pc"],
            self.trace.index(trace),
            trace["fn"],
        )


def _format_source(source: str, linenos: Tuple, path: Path, pc: int, idx: int, fn_name: str) -> str:
    ln = f" {color('bright blue')}{linenos[0]}"
    if linenos[1] > linenos[0]:
        ln = f"s{ln}{color('dark white')}-{color('bright blue')}{linenos[1]}"
    return (
        f"{color('dark white')}Trace step {color('bright blue')}{idx}{color('dark white')}, "
        f"program counter {color('bright blue')}{pc}{color('dark white')}:\n  {color('dark white')}"
        f"File {color('bright magenta')}\"{path}\"{color('dark white')}, line{ln}"
        f"{color('dark white')}, in {color('bright cyan')}{fn_name}{color('dark white')}:{source}"
    )


def _step_compare(a: Dict, b: Dict) -> bool:
    return a["depth"] == b["depth"] and a["jumpDepth"] == b["jumpDepth"]


def _check_last(trace_index: Sequence[Tuple]) -> Tuple[str, str]:
    initial = trace_index[0][1:]
    try:
        trace = next(i for i in trace_index[1:-1] if i[1:] == initial)
    except StopIteration:
        return "\u2514", "  "
    i = trace_index[1:].index(trace) + 2
    next_ = trace_index[i][1:]
    if next_[0] < initial[0] or (next_[0] == initial[0] and next_[1] <= initial[1]):
        return "\u2514", "  "
    return "\u251c", "\u2502 "


def _step_print(
    step: Dict,
    last_step: Dict,
    indent: Optional[str],
    start: Union[str, int],
    stop: Union[str, int],
) -> str:
    print_str = f"\n{color('dark white')}"
    if indent is not None:
        print_str += f"{indent}\u2500"
    if last_step["op"] in {"REVERT", "INVALID"} and _step_compare(step, last_step):
        contract_color = color("bright red")
    else:
        contract_color = color("bright magenta" if not step["jumpDepth"] else "")
    print_str += f"{contract_color}{step['fn']} {color('dark white')}{start}:{stop}{color}"
    if not step["jumpDepth"]:
        print_str += (
            f"  {color('dark white')}({color}{step['address']}{color('dark white')}){color}"
        )
    return print_str


def _get_memory(step: Dict, idx: int) -> HexBytes:
    offset = int(step["stack"][idx], 16) * 2
    length = int(step["stack"][idx - 1], 16) * 2
    return HexBytes("".join(step["memory"])[offset : offset + length])


def _get_last_map(address: EthAddress, sig: str) -> Dict:
    contract = _find_contract(address)
    last_map = {"address": EthAddress(address), "jumpDepth": 0, "name": None, "coverage": False}
    if contract:
        last_map.update(
            contract=contract,
            name=contract._name,
            fn=[f"{contract._name}.{contract.get_method(sig)}"],
        )
        if contract._build:
            last_map.update(pc_map=contract._build["pcMap"], coverage=True)
            if contract._build["language"] == "Solidity":
                last_map["active_branches"] = set()
    else:
        last_map.update(contract=None, fn=[f"<UnknownContract>.{sig}"])
    return last_map
