#!/usr/bin/python3

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type

import eth_abi
import psutil
import yaml
from hexbytes import HexBytes

import brownie
from brownie._config import _get_data_folder
from brownie.convert.utils import build_function_selector, get_type_strings

# network

ERROR_SIG = "0x08c379a0"


# error codes used in Solidity >=0.8.0
# docs.soliditylang.org/en/v0.8.0/control-structures.html#panic-via-assert-and-error-via-require
SOLIDITY_ERROR_CODES = {
    1: "Failed assertion",
    17: "Integer overflow",
    18: "Division or modulo by zero",
    33: "Conversion to enum out of bounds",
    24: "Access to storage byte array that is incorrectly encoded",
    49: "Pop from empty array",
    50: "Index out of range",
    65: "Attempted to allocate too much memory",
    81: "Call to zero-initialized variable of internal function type",
}


class UnknownAccount(Exception):
    pass


class UndeployedLibrary(Exception):
    pass


class UnsetENSName(Exception):
    pass


class IncompatibleEVMVersion(Exception):
    pass


class RPCProcessError(Exception):
    def __init__(self, cmd: str, uri: str) -> None:
        super().__init__(f"Unable to launch local RPC client.\nCommand: {cmd}\nURI: {uri}")


class RPCConnectionError(Exception):
    def __init__(self, cmd: str, proc: psutil.Popen, uri: str) -> None:
        msg = (
            "Able to launch RPC client, but unable to connect."
            f"\n\nCommand: {cmd}\nURI: {uri}\nExit Code: {proc.poll()}"
        )
        if sys.platform != "win32":
            out = proc.stdout.read().decode().strip() or "  (Empty)"
            err = proc.stderr.read().decode().strip() or "  (Empty)"
            msg = f"{msg}\n\nStdout:\n{out}\n\nStderr:\n{err}"
        super().__init__(msg)


class RPCRequestError(Exception):
    pass


class MainnetUndefined(Exception):
    pass


class VirtualMachineError(Exception):
    """
    Raised when a call to a contract causes an EVM exception.

    Attributes
    ----------
    message : str
        The full error message received from the RPC client.
    revert_msg : str
        The returned error string, if any.
    revert_type : str
        The error type.
    pc : int
        The program counter where the error was raised.
    txid : str
        The transaction ID that raised the error.
    """

    def __init__(self, exc: ValueError) -> None:
        self.txid: str = ""
        self.source: str = ""
        self.revert_type: str = ""
        self.pc: Optional[int] = None
        self.revert_msg: Optional[str] = None
        self.dev_revert_msg: Optional[str] = None

        try:
            exc = exc.args[0]
        except Exception:
            pass

        if not (isinstance(exc, dict) and "message" in exc):
            raise ValueError(str(exc)) from None

        if "data" not in exc:
            raise ValueError(exc["message"]) from None

        self.message: str = exc["message"].rstrip(".")

        if isinstance(exc["data"], str) and exc["data"].startswith("0x"):
            self.revert_type = "revert"
            self.revert_msg = decode_typed_error(exc["data"])
            return

        try:
            txid, data = next((k, v) for k, v in exc["data"].items() if k.startswith("0x"))
            self.revert_type = data["error"]
        except StopIteration:
            raise ValueError(exc["message"]) from None

        self.txid = txid
        self.source = ""
        self.pc = data.get("program_counter")
        if self.pc and self.revert_type == "revert":
            self.pc -= 1

        self.revert_msg = data.get("reason")
        if isinstance(data.get("reason"), str) and data["reason"].startswith("0x"):
            self.revert_msg = decode_typed_error(data["reason"])

        self.dev_revert_msg = brownie.project.build._get_dev_revert(self.pc)
        if self.revert_msg is None and self.revert_type in ("revert", "invalid opcode"):
            self.revert_msg = self.dev_revert_msg
        elif self.revert_msg == "Failed assertion":
            self.revert_msg = self.dev_revert_msg or self.revert_msg

    def __str__(self) -> str:
        if not hasattr(self, "revert_type"):
            return str(self.message)
        msg = self.revert_type
        if self.revert_msg:
            msg = f"{msg}: {self.revert_msg}"
        if self.source:
            msg = f"{msg}\n{self.source}"
        return str(msg)

    def _with_attr(self, **kwargs) -> "VirtualMachineError":
        for key, value in kwargs.items():
            setattr(self, key, value)
        if self.revert_msg == "Failed assertion":
            self.revert_msg = self.dev_revert_msg or self.revert_msg  # type: ignore
        return self


class TransactionError(Exception):
    pass


class EventLookupError(LookupError):
    pass


class NamespaceCollision(AttributeError):
    pass


# project/


class ContractExists(Exception):
    pass


class ContractNotFound(Exception):
    pass


class ProjectAlreadyLoaded(Exception):
    pass


class ProjectNotFound(Exception):
    pass


class BadProjectName(Exception):
    pass


class CompilerError(Exception):
    def __init__(self, e: Type[psutil.Popen], compiler: str = "Compiler") -> None:
        self.compiler = compiler

        err_json = yaml.safe_load(e.stdout_data)
        err = [i.get("formattedMessage") or i["message"] for i in err_json["errors"]]
        super().__init__(f"{compiler} returned the following errors:\n\n" + "\n".join(err))


class IncompatibleSolcVersion(Exception):
    pass


class IncompatibleVyperVersion(Exception):
    pass


class PragmaError(Exception):
    pass


class InvalidManifest(Exception):
    pass


class UnsupportedLanguage(Exception):
    pass


class InvalidPackage(Exception):
    pass


class BrownieEnvironmentError(Exception):
    pass


class BrownieCompilerWarning(Warning):
    pass


class BrownieEnvironmentWarning(Warning):
    pass


class InvalidArgumentWarning(BrownieEnvironmentWarning):
    pass


class BrownieTestWarning(Warning):
    pass


class BrownieConfigWarning(Warning):
    pass


def __get_path() -> Path:
    return _get_data_folder().joinpath("errors.json")


def parse_errors_from_abi(abi: List):
    updated = False
    for item in [i for i in abi if i.get("type", None) == "error"]:
        selector = build_function_selector(item)
        if selector in _errors:
            continue
        updated = True
        _errors[selector] = item

    if updated:
        with __get_path().open("w") as fp:
            json.dump(_errors, fp, sort_keys=True, indent=2)


_errors: Dict = {ERROR_SIG: {"name": "Error", "inputs": [{"name": "", "type": "string"}]}}

try:
    with __get_path().open() as fp:
        _errors.update(json.load(fp))
except (FileNotFoundError, json.decoder.JSONDecodeError):
    pass


def decode_typed_error(data: str) -> str:
    selector = data[:10]
    if selector == "0x4e487b71":
        # special case, solidity compiler panics
        error_code = int(HexBytes(data[10:]).hex(), 16)
        return SOLIDITY_ERROR_CODES.get(error_code, f"Unknown compiler Panic: {error_code}")
    if selector in _errors:
        types_list = get_type_strings(_errors[selector]["inputs"])
        result = eth_abi.decode(types_list, HexBytes(data)[4:])
        if selector == ERROR_SIG:
            return result[0]
        else:
            return f"{_errors[selector]['name']}: {', '.join([str(i) for i in result])}"
    else:
        return f"Unknown typed error: {data}"
