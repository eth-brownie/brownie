#!/usr/bin/python3

import functools
import sys
import threading
import time
from collections import OrderedDict
from hashlib import sha1
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import black
import requests
from eth_abi import decode_abi
from hexbytes import HexBytes
from web3.exceptions import TransactionNotFound

from brownie._config import CONFIG
from brownie.convert import EthAddress, Wei
from brownie.exceptions import RPCRequestError
from brownie.project import build
from brownie.project import main as project_main
from brownie.project.sources import highlight_source
from brownie.test import coverage
from brownie.utils import color
from brownie.utils.output import build_tree

from . import state
from .event import _decode_logs, _decode_trace
from .web3 import web3


def trace_property(fn: Callable) -> Any:
    # attributes that are only available after querying the tranasaction trace

    @property  # type: ignore
    def wrapper(self: "TransactionReceipt") -> Any:
        if self.status == -1:
            return None
        if self._trace_exc is not None:
            raise self._trace_exc
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

    functools.update_wrapper(wrapper, fn)
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
        confirmations: The number of blocks since the transaction was confirmed
        nonce: Transaction nonce
        block_number: Block number this transaction was included in
        timestamp: Timestamp of the block this transaction was included in
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

    # these are defined as class attributes to expose them in console completion hints
    block_number = None
    contract_address: Optional[str] = None
    contract_name = None
    fn_name = None
    gas_used = None
    logs = None
    nonce = None
    sender = None
    txid = None
    txindex = None

    def __init__(
        self,
        txid: Union[str, bytes],
        sender: Any = None,
        silent: bool = True,
        required_confs: int = 1,
        name: str = "",
        revert_data: Optional[Tuple] = None,
    ) -> None:
        """Instantiates a new TransactionReceipt object.

        Args:
            txid: hexstring transaction ID
            sender: sender as a hex string or Account object
            required_confs: the number of required confirmations before processing the receipt
            silent: toggles console verbosity (default True)
            name: contract function being called
            revert_data: (revert string, program counter, revert type)
        """
        self._silent = silent

        if isinstance(txid, bytes):
            txid = HexBytes(txid).hex()
        if not self._silent:
            print(f"Transaction sent: {color('bright blue')}{txid}{color}")

        # internal attributes
        self._trace_exc = None
        self._trace_origin = None
        self._raw_trace = None
        self._trace = None
        self._call_cost = 0
        self._events = None
        self._return_value = None
        self._revert_msg = None
        self._modified_state = None
        self._new_contracts = None
        self._internal_transfers = None
        self._subcalls: Optional[List[Dict]] = None
        self._confirmed = threading.Event()

        # attributes that can be set immediately
        self.sender = sender
        self.status = -1
        self.txid = txid
        self.contract_name = None
        self.fn_name = name

        if name and "." in name:
            self.contract_name, self.fn_name = name.split(".", maxsplit=1)

        # avoid querying the trace to get the revert string if possible
        self._revert_msg, self._revert_pc, revert_type = revert_data or (None, None, None)
        if self._revert_msg is None and revert_type not in ("revert", "invalid_opcode"):
            self._revert_msg = revert_type

        self._await_transaction(required_confs)

        # if coverage evaluation is active, evaluate the trace
        if (
            CONFIG.argv["coverage"]
            and not coverage._check_cached(self.coverage_hash)
            and self.trace
        ):
            self._expand_trace()

    def __repr__(self) -> str:
        c = {-1: "bright yellow", 0: "bright red", 1: None}
        return f"<Transaction '{color(c[self.status])}{self.txid}{color}'>"

    def __hash__(self) -> int:
        return hash(self.txid)

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
    def subcalls(self) -> Optional[List]:
        if self._subcalls is None:
            self._expand_trace()
        return self._subcalls

    @trace_property
    def trace(self) -> Optional[List]:
        if self._trace is None:
            self._expand_trace()
        return self._trace

    @property
    def timestamp(self) -> Optional[int]:
        if self.status == -1:
            return None
        return web3.eth.getBlock(self.block_number)["timestamp"]

    @property
    def confirmations(self) -> int:
        if not self.block_number:
            return 0
        return web3.eth.blockNumber - self.block_number + 1

    def wait(self, required_confs: int) -> None:
        if self.confirmations > required_confs:
            print(f"This transaction already has {self.confirmations} confirmations.")
            return

        while True:
            try:
                tx: Dict = web3.eth.getTransaction(self.txid)
                break
            except TransactionNotFound:
                time.sleep(0.5)

        self._await_confirmation(tx, required_confs)

    def _raise_if_reverted(self, exc: Any) -> None:
        if self.status or CONFIG.mode == "console":
            return
        if self._revert_msg is None:
            # no revert message and unable to check dev string - have to get trace
            self._expand_trace()
        if self.contract_address:
            source = ""
        elif CONFIG.argv["revert"]:
            source = self._traceback_string()
        else:
            source = self._error_string(1)
        raise exc._with_attr(source=source, revert_msg=self._revert_msg)

    def _await_transaction(self, required_confs: int = 1) -> None:
        # await tx showing in mempool
        while True:
            try:
                tx: Dict = web3.eth.getTransaction(self.txid)
                break
            except TransactionNotFound:
                if self.sender is None:
                    # if sender was not explicitly set, this transaction was
                    # not broadcasted locally and so likely doesn't exist
                    raise
                time.sleep(0.5)
        self._set_from_tx(tx)

        if not self._silent:
            print(
                f"  Gas price: {color('bright blue')}{self.gas_price / 10 ** 9}{color} gwei"
                f"   Gas limit: {color('bright blue')}{self.gas_limit}{color}"
            )

        # await confirmation of tx in a separate thread which is blocking if required_confs > 0
        confirm_thread = threading.Thread(
            target=self._await_confirmation, args=(tx, required_confs), daemon=True
        )
        confirm_thread.start()
        if required_confs > 0:
            confirm_thread.join()

    def _await_confirmation(self, tx: Dict, required_confs: int = 1) -> None:
        if not tx["blockNumber"] and not self._silent and required_confs > 0:
            if required_confs == 1:
                print("Waiting for confirmation...")
            else:
                sys.stdout.write(
                    f"\rRequired confirmations: {color('bright yellow')}0/"
                    f"{required_confs}{color}"
                )
                sys.stdout.flush()

        # await first confirmation
        receipt = web3.eth.waitForTransactionReceipt(self.txid, timeout=None, poll_latency=0.5)

        self.block_number = receipt["blockNumber"]
        # wait for more confirmations if required and handle uncle blocks
        remaining_confs = required_confs
        while remaining_confs > 0 and required_confs > 1:
            try:
                receipt = web3.eth.getTransactionReceipt(self.txid)
                self.block_number = receipt["blockNumber"]
            except TransactionNotFound:
                if not self._silent:
                    sys.stdout.write(f"\r{color('red')}Transaction was lost...{color}{' ' * 8}")
                    sys.stdout.flush()
                # check if tx is still in mempool, this will raise otherwise
                tx = web3.eth.getTransaction(self.txid)
                self.block_number = None
                return self._await_confirmation(tx, required_confs)
            if required_confs - self.confirmations != remaining_confs:
                remaining_confs = required_confs - self.confirmations
                if not self._silent:
                    sys.stdout.write(
                        f"\rRequired confirmations: {color('bright yellow')}{self.confirmations}/"
                        f"{required_confs}{color}  "
                    )
                    if remaining_confs == 0:
                        sys.stdout.write("\n")
                    sys.stdout.flush()
            if remaining_confs > 0:
                time.sleep(1)

        self._set_from_receipt(receipt)
        self._confirmed.set()
        if not self._silent and required_confs > 0:
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
        if not self.fn_name and state._find_contract(tx["to"]) is not None:
            contract = state._find_contract(tx["to"])
            self.contract_name = contract._name
            self.fn_name = contract.get_method(tx["input"])

    def _set_from_receipt(self, receipt: Dict) -> None:
        """Sets object attributes based on the transaction reciept."""
        self.block_number = receipt["blockNumber"]
        self.txindex = receipt["transactionIndex"]
        self.gas_used = receipt["gasUsed"]
        self.logs = receipt["logs"]
        self.status = receipt["status"]

        self.contract_address = receipt["contractAddress"]
        if self.contract_address and not self.contract_name:
            self.contract_name = "UnknownContract"

        base = (
            f"{self.nonce}{self.block_number}{self.sender}{self.receiver}"
            f"{self.value}{self.input}{self.status}{self.gas_used}{self.txindex}"
        )
        self.coverage_hash = sha1(base.encode()).hexdigest()

        if self.status:
            self._events = _decode_logs(receipt["logs"])
        if self.fn_name:
            state.TxHistory()._gas(self._full_name(), receipt["gasUsed"])

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
                "debug_traceTransaction", (self.txid, {"disableStorage": CONFIG.mode != "console"})
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            msg = f"Encountered a {type(e).__name__} while requesting "
            msg += "debug_traceTransaction. The local RPC client has likely crashed."
            if CONFIG.argv["coverage"]:
                msg += " If the error persists, add the skip_coverage fixture to this test."
            raise RPCRequestError(msg) from None

        if "error" in trace:
            self._modified_state = None
            self._trace_exc = RPCRequestError(trace["error"]["message"])
            raise self._trace_exc

        self._raw_trace = trace = trace["result"]["structLogs"]
        if not trace:
            self._modified_state = False
            return

        if isinstance(trace[0]["gas"], str):
            # handle traces where numeric values are returned as hex (Nethermind)
            for step in trace:
                step["gas"] = int(step["gas"], 16)
                step["gasCost"] = int.from_bytes(HexBytes(step["gasCost"]), "big", signed=True)
                step["pc"] = int(step["pc"], 16)

        if self.status:
            self._confirmed_trace(trace)
        else:
            self._reverted_trace(trace)

    def _confirmed_trace(self, trace: Sequence) -> None:
        self._modified_state = next((True for i in trace if i["op"] == "SSTORE"), False)

        if trace[-1]["op"] != "RETURN" or self.contract_address:
            return
        contract = state._find_contract(self.receiver)
        if contract:
            data = _get_memory(trace[-1], -1)
            fn = contract.get_method_object(self.input)
            self._return_value = fn.decode_output(data)

    def _reverted_trace(self, trace: Sequence) -> None:
        self._modified_state = False
        # get events from trace
        self._events = _decode_trace(trace, str(self.receiver or self.contract_address))
        if self.contract_address:
            step = next((i for i in trace if i["op"] == "CODECOPY"), None)
            if step is not None and int(step["stack"][-3], 16) > 24577:
                self._revert_msg = "exceeds EIP-170 size limit"
        if self._revert_msg is not None:
            return

        # iterate over revert instructions in reverse to find revert message
        for step in (i for i in trace[::-1] if i["op"] in ("REVERT", "INVALID")):
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
                pc_map = state._find_contract(step["address"])._build["pcMap"]
                # if this is the function selector revert, check for a jump
                if "first_revert" in pc_map[step["pc"]]:
                    i = trace.index(step) - 4
                    if trace[i]["pc"] != step["pc"] - 4:
                        step = trace[i]
                self._revert_msg = pc_map[step["pc"]]["dev"]
                return
            except (KeyError, AttributeError, TypeError):
                pass

        step = next(i for i in trace[::-1] if i["op"] in ("REVERT", "INVALID"))
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
        if self._raw_trace is None:
            self._get_trace()
        if self._trace is not None:
            # in case `_get_trace` also expanded the trace, do not repeat
            return

        self._trace = trace = self._raw_trace
        self._new_contracts = []
        self._internal_transfers = []
        self._subcalls = []
        if self.contract_address or not trace:
            coverage._add_transaction(self.coverage_hash, {})
            return

        if trace[0]["depth"] == 1:
            self._trace_origin = "geth"
            self._call_cost = self.gas_used - trace[0]["gas"] + trace[-1]["gas"]
            for t in trace:
                t["depth"] = t["depth"] - 1
        else:
            self._trace_origin = "ganache"
            if trace[0]["gasCost"] >= 21000:
                # in ganache <6.10.0, gas costs are shifted by one step - we can
                # identify this when the first step has a gas cost >= 21000
                self._call_cost = trace[0]["gasCost"]
                for i in range(len(trace) - 1):
                    trace[i]["gasCost"] = trace[i + 1]["gasCost"]
                trace[-1]["gasCost"] = 0
            else:
                self._call_cost = self.gas_used - trace[0]["gas"] + trace[-1]["gas"]

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
                    calldata = None
                    self._new_contracts.append(EthAddress(address))
                    if int(step["stack"][-1], 16):
                        self._add_internal_xfer(step["address"], address, step["stack"][-1])
                else:
                    # calling an existing contract
                    stack_idx = -4 if step["op"] in ("CALL", "CALLCODE") else -3
                    offset = int(step["stack"][stack_idx], 16)
                    length = int(step["stack"][stack_idx - 1], 16)
                    calldata = HexBytes("".join(step["memory"]))[offset : offset + length]
                    sig = calldata[:4].hex()
                    address = step["stack"][-2][-40:]

                last_map[trace[i]["depth"]] = _get_last_map(address, sig)
                coverage_eval.setdefault(last_map[trace[i]["depth"]]["name"], {})

                self._subcalls.append(
                    {"from": step["address"], "to": EthAddress(address), "op": step["op"]}
                )
                if step["op"] in ("CALL", "CALLCODE"):
                    self._subcalls[-1]["value"] = int(step["stack"][-3], 16)
                if calldata and last_map[trace[i]["depth"]].get("function"):
                    fn = last_map[trace[i]["depth"]]["function"]
                    zip_ = zip(fn.abi["inputs"], fn.decode_input(calldata))
                    self._subcalls[-1].update(
                        inputs={i[0]["name"]: i[1] for i in zip_},  # type:ignore
                        function=fn._input_sig,
                    )
                elif calldata:
                    self._subcalls[-1]["calldata"] = calldata.hex()

            # update trace from last_map
            last = last_map[trace[i]["depth"]]
            trace[i].update(
                address=last["address"],
                contractName=last["name"],
                fn=last["internal_calls"][-1],
                jumpDepth=last["jumpDepth"],
                source=False,
            )

            opcode = trace[i]["op"]
            if opcode == "CALL" and int(trace[i]["stack"][-3], 16):
                self._add_internal_xfer(
                    last["address"], trace[i]["stack"][-2][-40:], trace[i]["stack"][-3]
                )

            try:
                pc = last["pc_map"][trace[i]["pc"]]
            except (KeyError, TypeError):
                # we don't have enough information about this contract
                continue

            if trace[i]["depth"] and opcode in ("RETURN", "REVERT", "INVALID", "SELFDESTRUCT"):
                subcall: dict = next(
                    i for i in self._subcalls[::-1] if i["to"] == last["address"]  # type: ignore
                )

                if opcode == "RETURN":
                    returndata = _get_memory(trace[i], -1)
                    if returndata:
                        fn = last["function"]
                        try:
                            return_values = fn.decode_output(returndata)
                            if len(fn.abi["outputs"]) == 1:
                                return_values = (return_values,)
                            subcall["return_value"] = return_values
                        except Exception:
                            subcall["returndata"] = returndata.hex()
                    else:
                        subcall["return_value"] = None
                elif opcode == "SELFDESTRUCT":
                    subcall["selfdestruct"] = True
                else:
                    if opcode == "REVERT":
                        data = _get_memory(trace[i], -1)[4:]
                        if data:
                            subcall["revert_msg"] = decode_abi(["string"], data)[0]
                    if "revert_msg" not in subcall and "dev" in pc:
                        subcall["revert_msg"] = pc["dev"]

            if "path" not in pc:
                continue
            trace[i]["source"] = {"filename": last["path_map"][pc["path"]], "offset": pc["offset"]}

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
                    if fn != last["internal_calls"][-1]:
                        last["internal_calls"].append(fn)
                        last["jumpDepth"] += 1
                # jump 'o' is returning from an internal function
                elif last["jumpDepth"] > 0:
                    del last["internal_calls"][-1]
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

    def _get_trace_gas(self, start: int, stop: int) -> Tuple[int, int]:
        total_gas = 0
        internal_gas = 0
        is_internal = True
        trace = self.trace

        for i in range(start, stop):
            # Check if we are in a subfunction or not
            if is_internal and not _step_compare(trace[i], trace[start]):
                is_internal = False
                # For the internal gas tracking we ignore the gas passed to an external call
                if trace[i]["depth"] > trace[start]["depth"]:
                    internal_gas -= trace[i - 1]["gasCost"]
            elif not is_internal and _step_compare(trace[i], trace[start]):
                is_internal = True

            total_gas += trace[i]["gasCost"]
            if is_internal:
                internal_gas += trace[i]["gasCost"]

            # manually add gas refunds where they occur
            if trace[i]["op"] == "SSTORE" and int(trace[i]["stack"][-2], 16) == 0:
                # 15000 gas is refunded if a word is set to 0x0
                # Note: There is currently no way to check if the value was 0x0 before.
                # This will give an incorrect refund if 0x0 is assigned to 0x0.
                total_gas -= 15000
                if is_internal:
                    internal_gas -= 15000
            if trace[i]["op"] == "SELFDESTRUCT":
                # 24000 gas is refunded on selfdestruct
                total_gas -= 24000
                if is_internal:
                    internal_gas -= 24000

        # For external calls, add the remaining gas returned back
        if start > 0 and trace[start]["depth"] > trace[start - 1]["depth"]:
            total_gas += trace[start - 1]["gasCost"]
            internal_gas += trace[start - 1]["gasCost"]

        return internal_gas, total_gas

    @trace_inspection
    def call_trace(self, expand: bool = False) -> None:
        """
        Display the complete sequence of contracts and methods called during
        the transaction. The format:

        Contract.functionName  [instruction]  start:stop  [gas used]

        * start:stop are index values for the `trace` member of this object,
          showing the points where the call begins and ends
        * for calls that include subcalls, gas use is displayed as
          [gas used in this frame / gas used in this frame + subcalls]
        * Calls displayed in red ended with a `REVERT` or `INVALID` instruction.

        Arguments
        ---------
        expand : bool
            If `True`, show an expanded call trace including inputs and return values
        """

        trace = self.trace
        key = _step_internal(
            trace[0], trace[-1], 0, len(trace), self._get_trace_gas(0, len(self.trace))
        )

        call_tree: OrderedDict = OrderedDict({key: OrderedDict()})
        active_tree = [call_tree[key]]

        # (index, depth, jumpDepth) for relevent steps in the trace
        trace_index = [(0, 0, 0)] + [
            (i, trace[i]["depth"], trace[i]["jumpDepth"])
            for i in range(1, len(trace))
            if not _step_compare(trace[i], trace[i - 1])
        ]

        subcalls = self.subcalls[::-1]
        for i, (idx, depth, jump_depth) in enumerate(trace_index[1:], start=1):
            last = trace_index[i - 1]
            if depth == last[1] and jump_depth < last[2]:
                # returning from an internal function, reduce tree by one
                active_tree.pop()
                continue
            elif depth < last[1]:
                # returning from an external call, return tree by jumpDepth of the previous depth
                active_tree = active_tree[: -(last[2] + 1)]
                continue

            if depth > last[1]:
                # called to a new contract
                end = next((x[0] for x in trace_index[i + 1 :] if x[1] < depth), len(trace))
                total_gas, internal_gas = self._get_trace_gas(idx, end)
                key = _step_external(
                    trace[idx],
                    trace[end - 1],
                    idx,
                    end,
                    (total_gas, internal_gas),
                    subcalls.pop(),
                    expand,
                )
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

                total_gas, internal_gas = self._get_trace_gas(idx, end)
                key = _step_internal(
                    trace[idx], trace[end - 1], idx, end, (total_gas, internal_gas)
                )

            active_tree[-1][key] = OrderedDict()
            active_tree.append(active_tree[-1][key])

        print(
            f"Call trace for '{color('bright blue')}{self.txid}{color}':\n"
            f"Initial call cost  [{color('bright yellow')}{self._call_cost} gas{color}]"
        )
        print(build_tree(call_tree).rstrip())

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
        contract = state._find_contract(self.trace[idx]["address"])
        source, linenos = highlight_source(
            contract._sources.get(trace["source"]["filename"]), trace["source"]["offset"], pad
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


def _step_internal(
    step: Dict,
    last_step: Dict,
    start: Union[str, int],
    stop: Union[str, int],
    gas: Tuple[int, int],
    subcall: Dict = None,
) -> str:
    if last_step["op"] in {"REVERT", "INVALID"} and _step_compare(step, last_step):
        contract_color = color("bright red")
    else:
        contract_color = color("bright cyan") if not step["jumpDepth"] else color()
    key = f"{color('dark white')}{contract_color}{step['fn']}  {color('dark white')}"

    left_bracket = f"{color('dark white')}["
    right_bracket = f"{color('dark white')}]"

    if subcall:
        key = f"{key}[{color}{subcall['op']}{right_bracket}  "

    key = f"{key}{start}:{stop}{color}"

    if gas:
        if gas[0] == gas[1]:
            gas_str = f"{color('bright yellow')}{gas[0]} gas"
        else:
            gas_str = f"{color('bright yellow')}{gas[0]} / {gas[1]} gas"
        key = f"{key}  {left_bracket}{gas_str}{right_bracket}"

    if last_step["op"] == "SELFDESTRUCT":
        key = f"{key}  {left_bracket}{color('bright red')}SELFDESTRUCT{right_bracket}"

    return key


def _format(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        mode = black.FileMode(line_length=60)
        black.format_str(str(value), mode=mode)
    return str(value)


def _step_external(
    step: Dict,
    last_step: Dict,
    start: Union[str, int],
    stop: Union[str, int],
    gas: Tuple[int, int],
    subcall: Dict,
    expand: bool,
) -> str:
    key = _step_internal(step, last_step, start, stop, gas, subcall)
    if not expand:
        return key

    result: OrderedDict = OrderedDict({key: {}})
    result[key][f"address: {step['address']}"] = None

    if "value" in subcall:
        result[key][f"value: {subcall['value']}"] = None

    if "inputs" not in subcall:
        result[key][f"calldata: {subcall.get('calldata')}"] = None
    elif subcall["inputs"]:
        result[key]["input arguments:"] = [
            f"{k}: {_format(v)}" for k, v in subcall["inputs"].items()
        ]
    else:
        result[key]["input arguments: None"] = None

    if "return_value" in subcall:
        value = subcall["return_value"]
        if isinstance(value, tuple) and len(value) > 1:
            result[key]["return values:"] = [_format(i) for i in value]
        else:
            if isinstance(value, tuple):
                value = value[0]
            result[key][f"return value: {_format(value)}"] = None
    elif "returndata" in subcall:
        result[key][f"returndata: {subcall['returndata']}"] = None

    if "revert_msg" in subcall:
        result[key][f"revert reason: {color('bright red')}{subcall['revert_msg']}{color}"] = None

    return build_tree(result, multiline_pad=0).rstrip()


def _get_memory(step: Dict, idx: int) -> HexBytes:
    offset = int(step["stack"][idx], 16)
    length = int(step["stack"][idx - 1], 16)
    return HexBytes("".join(step["memory"]))[offset : offset + length]


def _get_last_map(address: EthAddress, sig: str) -> Dict:
    contract = state._find_contract(address)
    last_map = {"address": EthAddress(address), "jumpDepth": 0, "name": None, "coverage": False}

    if contract:
        if contract.get_method(sig):
            full_fn_name = f"{contract._name}.{contract.get_method(sig)}"
        else:
            full_fn_name = contract._name
        last_map.update(
            contract=contract,
            function=contract.get_method_object(sig),
            name=contract._name,
            internal_calls=[full_fn_name],
            path_map=contract._build.get("allSourcePaths"),
            pc_map=contract._build.get("pcMap"),
        )
        if isinstance(contract._project, project_main.Project):
            # only evaluate coverage for contracts that are part of a `Project`
            last_map["coverage"] = True
            if contract._build["language"] == "Solidity":
                last_map["active_branches"] = set()
    else:
        last_map.update(contract=None, internal_calls=[f"<UnknownContract>.{sig}"], pc_map=None)

    return last_map
