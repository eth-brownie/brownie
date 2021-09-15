#!/usr/bin/python3

import sys
from typing import Optional, Type

import eth_abi
import psutil
import yaml
from hexbytes import HexBytes

import brownie

# network


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
        try:
            exc = exc.args[0]
        except Exception:
            pass

        if isinstance(exc, dict) and "message" in exc:
            if "data" not in exc:
                raise ValueError(exc["message"]) from None

            self.message: str = exc["message"].rstrip(".")

            if isinstance(exc["data"], str):
                # handle parity exceptions - this logic probably is not perfect
                if "0x08c379a0" in exc["data"]:
                    revert_type, err_msg = [i.strip() for i in exc["data"].split("0x08c379a0", 1)]
                    err_msg = eth_abi.decode_abi(["string"], HexBytes(err_msg))
                    err_msg = f"{revert_type} '{err_msg}'"
                elif exc["data"].endswith("0x"):
                    err_msg = exc["data"][:-2].strip()
                else:
                    err_msg = exc["data"]
                raise ValueError(f"{self.message}: {err_msg}") from None

            try:
                txid, data = next((k, v) for k, v in exc["data"].items() if k.startswith("0x"))
            except StopIteration:
                raise ValueError(exc["message"]) from None

            self.txid: str = txid
            self.source: str = ""
            self.revert_type: str = data["error"]
            self.pc: Optional[str] = data.get("program_counter")
            if self.pc and self.revert_type == "revert":
                self.pc -= 1

            self.revert_msg: Optional[str] = data.get("reason")
            self.dev_revert_msg = brownie.project.build._get_dev_revert(self.pc)
            if self.revert_msg is None and self.revert_type in ("revert", "invalid opcode"):
                self.revert_msg = self.dev_revert_msg
            elif self.revert_msg == "Failed assertion":
                self.revert_msg = self.dev_revert_msg or self.revert_msg

        else:
            raise ValueError(str(exc)) from None

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
