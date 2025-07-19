#!/usr/bin/python3

import json
import sys
from pathlib import Path
from typing import Dict, Final, List, Optional, Type, final

import eth_abi
import psutil
import yaml
from eth_typing import ABIError, HexStr
from hexbytes import HexBytes

import brownie
from brownie._config import _get_data_folder
from brownie.convert.utils import build_function_selector, get_type_strings

# network

ERROR_SIG: Final[HexStr] = "0x08c379a0"  # type: ignore [assignment]


# error codes used in Solidity >=0.8.0
# docs.soliditylang.org/en/v0.8.0/control-structures.html#panic-via-assert-and-error-via-require
SOLIDITY_ERROR_CODES: Final = {
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


@final
class UnknownAccount(Exception):
    pass


@final
class UndeployedLibrary(Exception):
    pass


@final
class UnsetENSName(Exception):
    pass


@final
class IncompatibleEVMVersion(Exception):
    pass


@final
class RPCProcessError(Exception):
    def __init__(self, cmd: str, uri: str) -> None:
        super().__init__(f"Unable to launch local RPC client.\nCommand: {cmd}\nURI: {uri}")


@final
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


@final
class RPCRequestError(Exception):
    pass


@final
class MainnetUndefined(Exception):
    pass


@final
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
        self.txid: HexStr = ""
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

        exc_message: str = exc["message"]
        self.message: Final[str] = exc_message.rstrip(".")

        exc_data = exc["data"]
        if isinstance(exc_data, str) and exc_data.startswith("0x"):
            self.revert_type = "revert"
            self.revert_msg = decode_typed_error(exc_data)
            return

        try:
            txid, data = next((k, v) for k, v in exc_data.items() if k.startswith("0x"))
            self.revert_type = data["error"]
        except StopIteration:
            raise ValueError(exc["message"]) from None

        self.txid = txid
        self.source = ""
        self.pc = data.get("program_counter")
        if self.pc and self.revert_type == "revert":
            self.pc -= 1

        reason = data.get("reason")
        if isinstance(reason, str) and reason.startswith("0x"):
            self.revert_msg = decode_typed_error(reason)
        else:
            self.revert_msg = reason

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


@final
class TransactionError(Exception):
    pass


@final
class EventLookupError(LookupError):
    pass


@final
class NamespaceCollision(AttributeError):
    pass


# project/


@final
class ContractExists(Exception):
    pass


@final
class ContractNotFound(Exception):
    pass


@final
class ProjectAlreadyLoaded(Exception):
    pass


@final
class ProjectNotFound(Exception):
    pass


@final
class BadProjectName(Exception):
    pass


@final
class CompilerError(Exception):
    def __init__(self, e: Type[psutil.Popen], compiler: str = "Compiler") -> None:
        self.compiler: Final = compiler

        err_json: List[Dict[str, str]] = yaml.safe_load(e.stdout_data)
        err = [i.get("formattedMessage") or i["message"] for i in err_json["errors"]]
        super().__init__(f"{compiler} returned the following errors:\n\n" + "\n".join(err))


@final
class IncompatibleSolcVersion(Exception):
    pass


@final
class IncompatibleVyperVersion(Exception):
    pass


@final
class PragmaError(Exception):
    pass


@final
class InvalidManifest(Exception):
    pass


@final
class UnsupportedLanguage(Exception):
    pass


@final
class InvalidPackage(Exception):
    pass


@final
class BrownieEnvironmentError(Exception):
    pass


@final
class BrownieCompilerWarning(Warning):
    pass


class BrownieEnvironmentWarning(Warning):
    pass


@final
class InvalidArgumentWarning(BrownieEnvironmentWarning):
    pass


@final
class BrownieTestWarning(Warning):
    pass


@final
class BrownieConfigWarning(Warning):
    pass


def __get_path() -> Path:
    return _get_data_folder().joinpath("errors.json")


def parse_errors_from_abi(abi: List[ABIElement]):
    updated = False
    for item in abi:
        if item.get("type", "") == "error":
            selector = build_function_selector(item)
            if selector in _errors:
                continue
            updated = True
            _errors[selector] = item

    if updated:
        with __get_path().open("w") as fp:
            json.dump(_errors, fp, sort_keys=True, indent=2)

    
_errors: Dict[HexStr, ABIError] = {
    ERROR_SIG: {"name": "Error", "inputs": [{"name": "", "type": "string"}]}
}

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

    if selector not in _errors:
        return f"Unknown typed error: {data}"

    abi = _errors[selector]
    types_list = get_type_strings(abi["inputs"])
    result = eth_abi.decode(types_list, HexBytes(data)[4:])
    return (
        result[0]
        if selector == ERROR_SIG
        else f"{abi['name']}: {', '.join(str(r) for r in result)}"
    )
